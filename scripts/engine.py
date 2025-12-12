from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


# Root where processed CSVs + metrics live (relative to repo root)
PROCESSED_ROOT = Path("data/processed")
METRICS_ROOT = PROCESSED_ROOT / "metrics"


@dataclass
class RepMetrics:
    rep_index: int
    start_frame: Optional[int]
    peak_frame: Optional[int]
    end_frame: Optional[int]
    rom: Optional[float]
    duration_sec: Optional[float]
    tempo_up_sec: Optional[float]
    tempo_down_sec: Optional[float]


@dataclass
class RepAnalysis:
    quality: str  # "good" | "needs_tweak"
    message: str


@dataclass
class RepWithAnalysis:
    rep_index: int
    metrics: RepMetrics
    analysis: RepAnalysis


def _metrics_path_for_video(exercise: str, video_path: str) -> Path:
    """
    Resolve the metrics JSON path for a given raw video.

    Prefer the new layout:
        data/processed/metrics/{exercise}/{stem}_metrics.json

    but if that doesn't exist, fall back to the legacy layout:
        data/processed/{exercise}/{stem}_metrics.json
    """
    stem = Path(video_path).stem

    # New layout (data/processed/metrics/...)
    new_path = METRICS_ROOT / exercise / f"{stem}_metrics.json"
    if new_path.exists():
        return new_path

    # Legacy layout (data/processed/<exercise>/...)
    legacy_path = PROCESSED_ROOT / exercise / f"{stem}_metrics.json"
    return legacy_path



def _load_metrics_for_video(exercise: str, video_path: str | Path) -> Dict[str, Any]:
    metrics_file = _metrics_path_for_video(exercise, video_path)
    if not metrics_file.exists():
        raise FileNotFoundError(f"Metrics file missing: {metrics_file}")
    with metrics_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def _analyse_single_rep(exercise: str, rep_idx: int, rep_raw: Dict[str, Any]) -> RepWithAnalysis:
    """
    Turn a raw per-rep metrics dict from compute_rep_metrics into
    a RepWithAnalysis with simple rule-based feedback.
    """
    rm = RepMetrics(
        rep_index=rep_idx,
        start_frame=rep_raw.get("start_frame"),
        peak_frame=rep_raw.get("peak_frame"),
        end_frame=rep_raw.get("end_frame"),
        rom=rep_raw.get("rom"),
        duration_sec=rep_raw.get("duration_sec"),
        tempo_up_sec=rep_raw.get("tempo_up_sec"),
        tempo_down_sec=rep_raw.get("tempo_down_sec"),
    )

    msgs: List[str] = []
    quality = "good"

    rom = rm.rom
    dur = rm.duration_sec

    # Simple thresholds; we ALWAYS count the rep and only use these for feedback.
    if rom is not None and rom < 0.05:
        msgs.append("ROM is very small; try to perform a fuller range rep.")
        quality = "needs_tweak"

    if dur is not None and dur < 0.5:
        msgs.append("Rep is rushed; slow down the movement.")
        quality = "needs_tweak"

    if not msgs:
        msgs.append("Good rep execution.")

    ra = RepAnalysis(quality=quality, message=" ".join(msgs))
    return RepWithAnalysis(rep_index=rep_idx, metrics=rm, analysis=ra)


def _estimate_difficulty(
    exercise: str,
    n_reps: int,
    avg_rom: float,
    avg_dur: float,
) -> str:
    """
    Rough difficulty heuristic just so we have a stable label.
    Not central to the thesis.
    """
    if n_reps == 0:
        return "invalid"

    # Longer sets or very slow reps → harder
    if n_reps >= 10 or avg_dur >= 2.0:
        return "hard"

    # Very short ROM on average suggests technique / warmup → easy
    if avg_rom < 0.08 and n_reps <= 5:
        return "easy"

    return "moderate"


def _build_overall_text(exercise: str, n_reps: int) -> str:
    if n_reps == 0:
        return f"Detected no valid reps for {exercise}."
    if n_reps == 1:
        return f"Detected 1 rep for {exercise}."
    return f"Detected {n_reps} reps for {exercise}."


def _load_and_annotate_metrics(exercise: str, video_path: str | Path) -> Dict[str, Any]:
    """
    Core helper: load JSON metrics, attach per-rep analysis, and derive set-level stats.
    """
    m = _load_metrics_for_video(exercise, video_path)

    per_rep_raw: List[Dict[str, Any]] = m.get("per_rep", []) or []

    per_rep_annotated: List[Dict[str, Any]] = []
    for i, rep_raw in enumerate(per_rep_raw, start=1):
        rwa = _analyse_single_rep(exercise, i, rep_raw)
        per_rep_annotated.append(
            {
                "rep_index": rwa.rep_index,
                "metrics": {
                    "rep_index": rwa.metrics.rep_index,
                    "start_frame": rwa.metrics.start_frame,
                    "peak_frame": rwa.metrics.peak_frame,
                    "end_frame": rwa.metrics.end_frame,
                    "rom": rwa.metrics.rom,
                    "duration_sec": rwa.metrics.duration_sec,
                    "tempo_up_sec": rwa.metrics.tempo_up_sec,
                    "tempo_down_sec": rwa.metrics.tempo_down_sec,
                },
                "analysis": {
                    "quality": rwa.analysis.quality,
                    "message": rwa.analysis.message,
                },
            }
        )

    # IMPORTANT: for now we *always* count all detected reps from compute_rep_metrics.
    # No ROM/tempo filtering here – that comes later as a refinement.
    n_reps = int(m.get("n_reps", len(per_rep_raw)) or 0)
    if n_reps == 0 and per_rep_raw:
        # If JSON says 0 but we have per-rep entries, trust the list length.
        n_reps = len(per_rep_raw)

    avg_rom = float(m.get("avg_rom", 0.0) or 0.0)
    avg_dur = float(m.get("avg_duration_sec", 0.0) or 0.0)

    # Angle ROM is a dict like {"elbow": deg, ...}; keep it if present.
    avg_angle_rom = m.get("avg_angle_rom", None)

    difficulty = _estimate_difficulty(exercise, n_reps, avg_rom, avg_dur)
    overall = _build_overall_text(exercise, n_reps)

    return {
        "exercise": exercise,
        "video": str(video_path),
        "valid": True,
        "difficulty": difficulty,
        "n_reps": n_reps,
        "avg_rom": avg_rom,
        "avg_duration_sec": avg_dur,
        "avg_angle_rom": avg_angle_rom,
        "overall": overall,
        "per_rep": per_rep_annotated,
    }


def analyze_video(video_path: str | Path, exercise: str) -> Dict[str, Any]:
    """
    Public entry point used by run_cli.py and the Streamlit UI.
    Right now it is entirely driven by precomputed metrics JSON.
    """
    return _load_and_annotate_metrics(exercise, video_path)
