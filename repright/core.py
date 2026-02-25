from __future__ import annotations

from pathlib import Path
from typing import Tuple

from repright.analyzer import RepRightAnalyzer


def analyze(video_path: Path, exercise: str, run_dir: Path) -> Tuple[Path, Path, Path]:
    analyzer = RepRightAnalyzer()
    result = analyzer.run(video_path, exercise, options={"run_dir": run_dir})
    artifacts = result.get("artifacts_v1", {})
    return Path(artifacts["analysis_json"]), Path(artifacts["overlay_path"] or ""), Path(artifacts["metrics_path"])
