from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ui.config.tokens import QUALITY_ZONES


@dataclass
class QualityViewModel:
    score: int | None
    color: str
    zone_label: str
    bg: str
    ring: str


@dataclass
class SummaryMetric:
    label: str
    value: str | int


def canonical_lift_quality(analysis: dict[str, Any] | None) -> int | None:
    if not isinstance(analysis, dict):
        return None
    summary = analysis.get("set_summary_v1")
    if not isinstance(summary, dict):
        return None
    score = summary.get("quality_score")
    if score is None:
        score = summary.get("quality_score_pct")
    return int(score) if isinstance(score, (int, float)) else None


def safe_summary(analysis: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(analysis, dict):
        return {}
    summary = analysis.get("set_summary_v1")
    return summary if isinstance(summary, dict) else {}


def quality_view_model(
    analysis: dict[str, Any] | None,
    response: dict[str, Any] | None,
) -> QualityViewModel:
    structured = (response or {}).get("structured") if isinstance(response, dict) else {}
    score = structured.get("overall_score") if isinstance(structured, dict) else None
    if score is None:
        score = canonical_lift_quality(analysis)

    if score is None:
        zone = QUALITY_ZONES["none"]
    elif score >= 80:
        zone = QUALITY_ZONES["green"]
    elif score >= 50:
        zone = QUALITY_ZONES["yellow"]
    else:
        zone = QUALITY_ZONES["red"]

    return QualityViewModel(
        score=score,
        color=zone["color"],
        zone_label=zone["label"],
        bg=zone["bg"],
        ring=zone["ring"],
    )


def summary_metrics(summary: dict[str, Any]) -> list[SummaryMetric]:
    avg_rom = summary.get("avg_rom")
    avg_rom_str = f"{avg_rom:.1f}°" if isinstance(avg_rom, (int, float)) else "n/a"
    return [
        SummaryMetric(label="Reps",           value=summary.get("n_reps", "n/a")),
        SummaryMetric(label="Avg ROM",        value=avg_rom_str),
        SummaryMetric(label="Low conf. reps", value=summary.get("n_low_confidence", "n/a")),
    ]


def top_fault_rows(summary: dict[str, Any], limit: int = 5) -> list[str]:
    faults = summary.get("top_faults") if isinstance(summary.get("top_faults"), list) else []
    rows: list[str] = []
    for tf in faults[:limit]:
        if isinstance(tf, dict):
            rows.append(
                f"- {tf.get('code', 'UNKNOWN')} × {tf.get('count', 0)}"
                f" (max severity: {tf.get('severity_max', 'info')})"
            )
    return rows


def artifact_analysis_json_path(analysis: dict[str, Any] | None) -> Path | None:
    artifacts = (analysis or {}).get("artifacts_v1") if isinstance(analysis, dict) else {}
    path = artifacts.get("analysis_json") if isinstance(artifacts, dict) else None
    if path and Path(str(path)).exists():
        return Path(str(path))
    return None


def resolve_overlay_path(
    payload: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
) -> Path | None:
    candidates = [
        ((payload or {}).get("highlights") or {}).get("overlay_path"),
        (analysis.get("artifacts_v1") or {}).get("overlay_path") if isinstance(analysis, dict) else None,
        analysis.get("overlay_path") if isinstance(analysis, dict) else None,
    ]
    for c in candidates:
        if not c:
            continue
        p = Path(str(c))
        try:
            if p.exists() and p.stat().st_size > 0:
                return p
        except Exception:
            continue
    return None
