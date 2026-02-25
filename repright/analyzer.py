from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
        analysis["artifacts_v1"] = {
            "analysis_json": str(Path(analysis_json_path).resolve()),
            "overlay_path": str(Path(overlay_path).resolve()) if Path(overlay_path).exists() else None,
            "metrics_path": str(Path(analysis_json_path).resolve()),
            "run_dir": str(resolved_run_dir.resolve()),
        }

        final_out = Path(out_path) if out_path else Path(analysis_json_path)
        final_out.parent.mkdir(parents=True, exist_ok=True)
        final_out.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        return analysis
