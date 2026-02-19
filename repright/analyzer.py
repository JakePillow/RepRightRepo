from __future__ import annotations

import json
import time
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from repright.pose_extract import extract_pose_npz

# Reuse proven rep logic from scripts/compute_rep_metrics.py (single-video, in-process)
from scripts.compute_rep_metrics import (
    choose_best_signal,
    per_exercise_params,
    detect_reps_low_to_high,
    compute_rep_metrics,
)


@dataclass
class RepRightAnalyzer:
    processed_root: Path = Path("data/processed")
    uploads_root: Path = Path("data/uploads")
    python_exe: Optional[str] = None  # if None, uses current interpreter

    def _py(self) -> str:
        return self.python_exe or shutil.which("python") or "python"

    def _stage_upload(self, video_path: Path, exercise: str) -> Path:
        """
        Copy to uploads/ with an exercise-tagged filename so downstream inference is stable.
        """
        video_path = Path(video_path)
        ex = (exercise or "").strip().lower()
        self.uploads_root.mkdir(parents=True, exist_ok=True)

        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe_stem = video_path.stem.replace(" ", "_")
        out_name = f"{stamp}_{ex}_{safe_stem}{video_path.suffix}"
        out_path = self.uploads_root / out_name

        if video_path.resolve() != out_path.resolve():
            out_path.write_bytes(video_path.read_bytes())

        return out_path

    def _metrics_path(self, stem: str, exercise: str) -> Path:
        ex = (exercise or "").strip().lower()
        out_dir = self.processed_root / "metrics" / ex
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f"{stem}_metrics.json"

    def _compute_metrics_single(self, npz_path: Path, meta_path: Path, exercise: str, stem_for_metrics: str) -> Path:
        ex = (exercise or "").strip().lower()
        metrics_path = self._metrics_path(stem_for_metrics, ex)

        pose = np.load(npz_path)["pose"]
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        fps = float(meta.get("fps", 30.0) or 30.0)

        sig, driver = choose_best_signal(pose, ex)
        sig = np.asarray(sig, float)

        low, high, min_rep_sec = per_exercise_params(ex)
        reps = detect_reps_low_to_high(sig, fps=fps, low=low, high=high, min_rep_sec=min_rep_sec)
        metrics_out = compute_rep_metrics(sig, reps, fps, pose=pose, exercise=ex, low=low, high=high)

        # Backward compatible:
        # - old compute_rep_metrics returns List[dict]
        # - newer versions may return {"reps":[...], "set_summary_v1":{...}}
        if isinstance(metrics_out, dict):
            rep_metrics = metrics_out.get("reps", [])
            set_summary_v1 = metrics_out.get("set_summary_v1", {})
        else:
            rep_metrics = metrics_out
            set_summary_v1 = {}
        summary = {
            "exercise": ex,
            "driver": driver,
            "source_npz": str(npz_path).replace("\\", "/"),
            "source_meta": str(meta_path).replace("\\", "/"),
            "fps": fps,
            "n_frames": int(pose.shape[0]),
            "n_reps": len(rep_metrics),
            "reps": rep_metrics,
            "set_summary_v1": set_summary_v1,
        }

        metrics_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return metrics_path

    def _overlay_paths_for_npz(self, npz_path: Path) -> Tuple[Path, Path]:
        """
        We generate tmp (mp4v) then transcode to final (h264) for browser reliability.
        """
        base = Path(npz_path).with_suffix("")  # remove .npz
        tmp_mp4v = Path(str(base) + "_overlay_tmp.mp4")
        final_mp4 = Path(str(base) + "_overlay.mp4")
        return tmp_mp4v, final_mp4

    def _ensure_overlay(self, video_path: Path, npz_path: Path) -> str:
        """
        Ensure overlay exists and is non-empty. Returns '' if generation fails.
        """
        tmp_mp4v, final_mp4 = self._overlay_paths_for_npz(npz_path)

        # If final already exists and non-empty, trust it
        if final_mp4.exists() and final_mp4.stat().st_size > 0:
            return str(final_mp4).replace("\\", "/")

        # Generate tmp overlay (mp4v) from NPZ
        try:
            cmd = [
                self._py(),
                "scripts/make_overlay_from_npz.py",
                "--video", str(video_path),
                "--npz", str(npz_path),
                "--out", str(tmp_mp4v),
            ]
            subprocess.run(cmd, check=True)
        except Exception:
            return ""

        if (not tmp_mp4v.exists()) or tmp_mp4v.stat().st_size == 0:
            return ""

        # Transcode to H.264 using ffmpeg if available (best for Streamlit/Chrome)
        ff = shutil.which("ffmpeg")
        if ff:
            try:
                cmd2 = [
                    ff, "-y",
                    "-i", str(tmp_mp4v),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    str(final_mp4),
                ]
                subprocess.run(cmd2, check=True)
            except Exception:
                # fallback: if transcode fails, at least return tmp_mp4v
                return str(tmp_mp4v).replace("\\", "/")

            if final_mp4.exists() and final_mp4.stat().st_size > 0:
                return str(final_mp4).replace("\\", "/")

        # If no ffmpeg, return tmp_mp4v
        return str(tmp_mp4v).replace("\\", "/") if tmp_mp4v.exists() and tmp_mp4v.stat().st_size > 0 else ""

    def analyze(self, video_path: str, exercise: str) -> Dict[str, Any]:
        ex = (exercise or "").strip().lower()
        vp = Path(video_path)

        # Stage upload to stable name
        staged = self._stage_upload(vp, ex)
        stem = staged.stem

        metrics_path = self._metrics_path(stem, ex)

        # If metrics missing, extract pose + compute metrics
        if not metrics_path.exists():
            npz_path, meta_path = extract_pose_npz(staged, ex, processed_root=self.processed_root)
            metrics_path = self._compute_metrics_single(npz_path, meta_path, ex, stem_for_metrics=stem)

        # Load metrics (even cached) so we can locate source_npz and ensure overlay
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        src_npz = (data.get("source_npz") or "").replace("\\", "/")
        npz_path2 = Path(src_npz) if src_npz else None

        overlay_path = ""
        if npz_path2 and npz_path2.exists():
            overlay_path = self._ensure_overlay(staged, npz_path2)

        # Stable schema return for UI + demo
        out: Dict[str, Any] = {
            "schema_version": "analysis_v1",
            "exercise": ex,
            "video_path": str(staged).replace("\\", "/"),
            "driver": data.get("driver", ""),
            "fps": float(data.get("fps", 30.0) or 30.0),
            "n_frames": int(data.get("n_frames", 0) or 0),
            "n_reps": int(data.get("n_reps", 0) or 0),
            "metrics_path": str(metrics_path).replace("\\", "/"),
            "overlay_path": overlay_path,
            "reps": data.get("reps", []),
            "raw": data,
        }
        return out







