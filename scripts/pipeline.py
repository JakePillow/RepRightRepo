from __future__ import annotations

import json
import time
from pathlib import Path

import cv2

MIN_VALID_OVERLAY_BYTES = 50 * 1024

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT = REPO_ROOT / "storage" / "runs"
RUNS_ROOT.mkdir(parents=True, exist_ok=True)


def new_run_dir(video_path: Path, exercise: str) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_stem = video_path.stem.replace(":", "_").replace("/", "_").replace("\\", "_")
    d = RUNS_ROOT / f"{stamp}_{exercise}_{safe_stem}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pick_first(run_dir: Path, patterns: list[str]) -> Path | None:
    for pat in patterns:
        hits = sorted(run_dir.glob(pat), key=lambda p: p.stat().st_mtime, reverse=True)
        if hits:
            return hits[0]
    return None


def _is_valid_overlay(path: Path | None, min_bytes: int = MIN_VALID_OVERLAY_BYTES) -> bool:
    if not path or not path.exists() or path.stat().st_size < min_bytes:
        return False
    cap = cv2.VideoCapture(str(path))
    try:
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        return frame_count > 0
    finally:
        cap.release()


def run_full_pipeline(video_path: Path, exercise: str, run_dir: Path | None = None) -> tuple[Path, Path, Path]:
    run_dir = run_dir or new_run_dir(video_path, exercise)

    from scripts import extract_all
    from scripts.compute_rep_metrics import compute_rep_metrics_file

    extract_all.process_video(video_path, run_dir, label_override=exercise)

    poses_jsonl = _pick_first(run_dir, [f"{video_path.stem}*.jsonl", "*.jsonl"])
    if poses_jsonl is None:
        raise RuntimeError("Pose extraction failed (no jsonl produced).")

    overlay_video = _pick_first(
        run_dir,
        [f"{video_path.stem}*_overlay.mp4", f"{video_path.stem}*_overlay.webm", "*_overlay.mp4", "*_overlay.webm", "*overlay*.mp4", "*overlay*.webm"],
    )
    if not _is_valid_overlay(overlay_video):
        if overlay_video is not None and overlay_video.exists():
            print(f"[warn] Overlay looks invalid ({overlay_video.stat().st_size} bytes): {overlay_video}")
        overlay_video = run_dir / "MISSING_OVERLAY.mp4"

    summary_json = _pick_first(run_dir, [f"{video_path.stem}*_summary.json", "*_summary.json"])
    fps = 25.0
    if summary_json and summary_json.exists():
        try:
            s = json.loads(summary_json.read_text(encoding="utf-8"))
            fps = float(s.get("fps", fps))
        except Exception:
            pass

    metrics_json = run_dir / "analysis_v1.json"
    compute_rep_metrics_file(exercise, poses_jsonl, metrics_json, fps=fps)

    analysis = json.loads(metrics_json.read_text(encoding="utf-8"))
    overlay_abs = str(overlay_video.resolve()) if _is_valid_overlay(overlay_video) else None
    analysis["overlay_path"] = overlay_abs
    analysis["artifacts_v1"] = {
        "analysis_json": str(metrics_json.resolve()),
        "overlay_path": overlay_abs,
        "metrics_path": str(metrics_json.resolve()),
        "run_dir": str(run_dir.resolve()),
    }
    metrics_json.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    return overlay_video, metrics_json, run_dir
