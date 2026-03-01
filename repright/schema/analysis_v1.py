from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, TypedDict


SchemaVersion = Literal["analysis_v1"]
ConfidenceLevel = Literal["high", "medium", "low"]
FaultSeverity = Literal["info", "warn", "error"]


class ConfidenceV1(TypedDict, total=False):
    level: ConfidenceLevel
    reasons: List[str]


class FaultV1(TypedDict, total=False):
    code: str
    severity: FaultSeverity
    value: float
    threshold: float
    evidence: str


class AngleMetricV1(TypedDict, total=False):
    side: str                  # "L" or "R" or "avg"
    min_deg: float
    max_deg: float
    rom_deg: float
    valid_frac: float          # fraction of frames valid (not NaN)


class BiomechV1(TypedDict, total=False):
    angles: Dict[str, AngleMetricV1]  # e.g. {"elbow": {...}}


class RepV1(TypedDict, total=False):
    rep_index: int
    start_frame: int
    peak_frame: int
    end_frame: int

    rom: float
    duration_sec: float
    tempo_up_sec: float
    tempo_down_sec: float

    confidence_v1: ConfidenceV1
    biomech_v1: BiomechV1
    faults_v1: List[FaultV1]

    # for truncated / inferred cases
    tempo_down_inferred: bool
    tempo_down_sec_inferred: float
    end_frame_source: str


class SetSummaryV1(TypedDict, total=False):
    n_reps: int
    avg_rom: float
    avg_duration_sec: float
    avg_tempo_up_sec: float
    avg_tempo_down_sec: float

    # counts of common conditions
    n_low_confidence: int
    n_inferred_eccentric: int

    # faults aggregation
    fault_counts: Dict[str, int]
    top_faults: List[Dict[str, Any]]  # [{"code":..., "count":..., "severity_max":...}, ...]
    quality_score_pct: int
    quality_band: Literal["green", "yellow", "red"]


class AnalysisV1(TypedDict, total=False):
    schema_version: SchemaVersion
    exercise: str
    video_path: str
    driver: str
    fps: float
    n_frames: int
    n_reps: int
    metrics_path: str
    overlay_path: str

    reps: List[RepV1]
    set_summary_v1: SetSummaryV1

    raw: Dict[str, Any]  # keep raw metrics for debugging / future upgrades
