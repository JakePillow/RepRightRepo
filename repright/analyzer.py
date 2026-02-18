from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional, List

VALID_EXERCISES = {"bench", "squat", "curl", "deadlift"}


@dataclass
class AnalysisV1:
    schema_version: str
    video_rel: str
    exercise: str

    n_reps: int
    fps: float
    n_frames: int
    driver: str

    reps: List[Dict[str, Any]]

    avg_rom: float
    avg_rep_duration_sec: float

    sources: Dict[str, Any]
    warnings: List[str]


class RepRightAnalyzer:

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        processed_root: Path = Path("data/processed"),
        reports_root: Path = Path("data/reports"),
    ) -> None:
        self.repo_root = repo_root or Path(".").resolve()
        self.processed_root = (self.repo_root / processed_root).resolve()
        self.reports_root = (self.repo_root / reports_root).resolve()
        self.reports_root.mkdir(parents=True, exist_ok=True)

    def _metrics_path_for_video(self, video_rel: str, exercise: str) -> Path:
        stem = Path(video_rel).stem
        return self.processed_root / "metrics" / exercise / f"{stem}_metrics.json"

    def analyze(
        self,
        video_rel: str,
        exercise: str,
        out_path: Optional[Path] = None,
    ) -> Dict[str, Any]:

        exercise = (exercise or "").lower().strip()
        if exercise not in VALID_EXERCISES:
            raise ValueError(f"Invalid exercise: {exercise}")

        video_rel = (video_rel or "").replace("\\", "/").strip()
        if not video_rel:
            raise ValueError("video_rel is empty")

        warnings: List[str] = []

        metrics_path = self._metrics_path_for_video(video_rel, exercise)
        if not metrics_path.exists():
            raise FileNotFoundError(f"Missing metrics JSON: {metrics_path}")

        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

        reps = metrics.get("reps") or []
        n_reps = int(metrics.get("n_reps", len(reps)) or 0)
        fps = float(metrics.get("fps", 30.0) or 30.0)
        n_frames = int(metrics.get("n_frames", 0) or 0)
        driver = str(metrics.get("driver", "") or "")

        roms = [float(r.get("rom", 0.0) or 0.0) for r in reps]
        durs = [float(r.get("duration_sec", 0.0) or 0.0) for r in reps]

        avg_rom = sum(roms) / len(roms) if roms else 0.0
        avg_rep_dur = sum(durs) / len(durs) if durs else 0.0

        analysis = AnalysisV1(
            schema_version="analysis_v1",
            video_rel=video_rel,
            exercise=exercise,
            n_reps=n_reps,
            fps=fps,
            n_frames=n_frames,
            driver=driver,
            reps=reps,
            avg_rom=float(avg_rom),
            avg_rep_duration_sec=float(avg_rep_dur),
            sources={
                "metrics_json": str(metrics_path.as_posix()),
                "source_npz": metrics.get("source_npz"),
                "source_meta": metrics.get("source_meta"),
            },
            warnings=warnings,
        )

        out_obj = asdict(analysis)

        if out_path is None:
            stem = Path(video_rel).stem
            out_path = self.reports_root / f"analysis_{exercise}_{stem}.json"

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(out_obj, indent=2), encoding="utf-8")

        return out_obj
