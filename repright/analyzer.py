from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2

MIN_VALID_OVERLAY_BYTES = 50 * 1024

from scripts.pipeline import new_run_dir, run_full_pipeline


class RepRightAnalyzer:
    def __init__(self, output_root: Path | None = None) -> None:
        self.output_root = output_root or (Path(__file__).resolve().parents[1] / "storage" / "runs")
        self.output_root.mkdir(parents=True, exist_ok=True)

    def run(
        self,
        video_path: str | Path,
        exercise_label: str,
        out_path: str | Path | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        options = options or {}
        video = Path(video_path)
        if not video.exists():
            raise FileNotFoundError(f"Video not found: {video}")
        if exercise_label not in {"bench", "curl", "deadlift", "squat"}:
            raise ValueError(f"Unsupported exercise: {exercise_label}")

        run_dir = Path(options.get("run_dir")) if options.get("run_dir") else new_run_dir(video, exercise_label)
        overlay_path, analysis_json_path, resolved_run_dir = run_full_pipeline(video, exercise_label, run_dir)

        analysis = json.loads(Path(analysis_json_path).read_text(encoding="utf-8"))
        overlay_file = Path(overlay_path)
        overlay_valid = False
        if overlay_file.exists() and overlay_file.stat().st_size >= MIN_VALID_OVERLAY_BYTES:
            cap = cv2.VideoCapture(str(overlay_file))
            try:
                overlay_valid = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) > 0
            finally:
                cap.release()
        if not overlay_valid and overlay_file.exists():
            print(f"[warn] overlay invalid after write: {overlay_file} ({overlay_file.stat().st_size} bytes)")

        artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}
        artifacts.update(
            {
                "analysis_json": str(Path(analysis_json_path).resolve()),
                "overlay_path": str(overlay_file.resolve()) if overlay_valid else None,
                "metrics_path": str(Path(analysis_json_path).resolve()),
                "run_dir": str(resolved_run_dir.resolve()),
            }
        )
        analysis["overlay_path"] = artifacts["overlay_path"]
        analysis["artifacts_v1"] = artifacts

        final_out = Path(out_path) if out_path else Path(analysis_json_path)
        final_out.parent.mkdir(parents=True, exist_ok=True)
        final_out.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        return analysis
