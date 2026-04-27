from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from repright.analyser import RepRightAnalyzer


def analyze(video_path: Path, exercise: str, run_dir: Path) -> Dict[str, Any]:
    analyzer = RepRightAnalyzer()
    result = analyzer.run(video_path, exercise, options={"run_dir": run_dir})
    return result
