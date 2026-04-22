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


@dataclass
class ComparisonMetricView:
    label: str
    previous: str
    current: str
    delta: str
    trend: str
    tone: str


@dataclass
class ComparisonViewModel:
    headline: str
    summary: str
    metrics: list[ComparisonMetricView]
    fault_rows: list[str]


def canonical_lift_quality(analysis: dict[str, Any] | None) -> int | None:
    if not isinstance(analysis, dict):
        return None
    summary = analysis.get("set_summary_v1")
    if not isinstance(summary, dict):
        return None
    score = summary.get("quality_score") or summary.get("quality_score_pct")
    return int(score) if isinstance(score, (int, float)) else None


def safe_summary(analysis: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(analysis, dict):
        return {}
    summary = analysis.get("set_summary_v1")
    return summary if isinstance(summary, dict) else {}


def quality_view_model(analysis, response) -> QualityViewModel:
    structured = (response or {}).get("structured") if isinstance(response, dict) else {}
    score = structured.get("overall_score") if isinstance(structured, dict) else None
    if score is None:
        score = canonical_lift_quality(analysis)
    zone = (
        QUALITY_ZONES["green"]  if isinstance(score, int) and score >= 80 else
        QUALITY_ZONES["yellow"] if isinstance(score, int) and score >= 50 else
        QUALITY_ZONES["red"]    if isinstance(score, int) else
        QUALITY_ZONES["none"]
    )
    return QualityViewModel(score=score, color=zone["color"], zone_label=zone["label"],
                            bg=zone["bg"], ring=zone["ring"])


def summary_metrics(summary: dict[str, Any]) -> list[SummaryMetric]:
    avg_rom = summary.get("avg_rom")
    avg_rom_str = f"{avg_rom:.1f}°" if isinstance(avg_rom, (int, float)) else "n/a"
    return [
        SummaryMetric("Reps",           summary.get("n_reps", "n/a")),
        SummaryMetric("Avg ROM",        avg_rom_str),
        SummaryMetric("Low conf. reps", summary.get("n_low_confidence", "n/a")),
    ]


def top_fault_rows(summary: dict[str, Any], limit: int = 5) -> list[str]:
    faults = summary.get("top_faults") if isinstance(summary.get("top_faults"), list) else []
    return [
        f"- {tf.get('code','UNKNOWN')} × {tf.get('count',0)} (max: {tf.get('severity_max','info')})"
        for tf in faults[:limit] if isinstance(tf, dict)
    ]


def artifact_analysis_json_path(analysis) -> Path | None:
    artifacts = (analysis or {}).get("artifacts_v1") if isinstance(analysis, dict) else {}
    path = artifacts.get("analysis_json") if isinstance(artifacts, dict) else None
    if path and Path(str(path)).exists():
        return Path(str(path))
    return None


def _as_float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def _format_value(metric: str, value: Any) -> str:
    if value is None:
        return "n/a"
    if metric in {"quality_score", "n_reps", "n_low_confidence"} and isinstance(value, (int, float)):
        return str(int(round(float(value))))
    if metric == "load_kg" and isinstance(value, (int, float)):
        return f"{float(value):.1f} kg"
    if metric in {"avg_rom", "avg_duration_sec", "avg_tempo_up_sec", "avg_tempo_down_sec"} and isinstance(value, (int, float)):
        suffix = "°" if metric == "avg_rom" else "s"
        return f"{float(value):.2f}{suffix}"
    return str(value)


def _format_delta(metric: str, delta: Any) -> str:
    if not isinstance(delta, (int, float)):
        return "n/a"
    if abs(float(delta)) < 1e-6:
        return "No change"
    prefix = "+" if float(delta) > 0 else ""
    if metric == "load_kg":
        return f"{prefix}{float(delta):.1f} kg"
    if metric == "avg_rom":
        return f"{prefix}{float(delta):.2f}°"
    if metric in {"avg_duration_sec", "avg_tempo_up_sec", "avg_tempo_down_sec"}:
        return f"{prefix}{float(delta):.2f}s"
    if metric in {"quality_score", "n_reps", "n_low_confidence"}:
        return f"{prefix}{int(round(float(delta)))}"
    return f"{prefix}{float(delta):.2f}"


def _metric_tone(metric: str, trend: str) -> str:
    if trend == "stable":
        return "neutral"
    if trend == "improved":
        return "good"
    if trend == "regressed":
        return "bad"
    return "neutral"


def comparison_view_model(payload: dict[str, Any] | None) -> ComparisonViewModel | None:
    if not isinstance(payload, dict):
        return None
    comparison = payload.get("comparison_v1")
    if not isinstance(comparison, dict):
        return None
    if comparison.get("exercise_match") is False:
        return None

    previous = comparison.get("previous") if isinstance(comparison.get("previous"), dict) else {}
    current = comparison.get("current") if isinstance(comparison.get("current"), dict) else {}
    delta = comparison.get("delta") if isinstance(comparison.get("delta"), dict) else {}
    trend = comparison.get("trend") if isinstance(comparison.get("trend"), dict) else {}

    metric_specs = [
        ("quality_score", "Quality"),
        ("avg_rom", "Avg ROM"),
        ("n_reps", "Reps"),
        ("n_low_confidence", "Low conf."),
        ("load_kg", "Load"),
    ]
    metrics: list[ComparisonMetricView] = []
    for key, label in metric_specs:
        prev_value = previous.get(key)
        curr_value = current.get(key)
        delta_value = delta.get(key)
        if prev_value is None and curr_value is None and delta_value is None:
            continue
        metric_trend = str(trend.get(key) or "stable")
        if key not in trend and isinstance(delta_value, (int, float)):
            if abs(float(delta_value)) < 1e-6:
                metric_trend = "stable"
            else:
                metric_trend = "improved" if float(delta_value) > 0 else "regressed"
                if key == "n_low_confidence":
                    metric_trend = "improved" if float(delta_value) < 0 else "regressed"
        metrics.append(
            ComparisonMetricView(
                label=label,
                previous=_format_value(key, prev_value),
                current=_format_value(key, curr_value),
                delta=_format_delta(key, delta_value),
                trend=metric_trend,
                tone=_metric_tone(key, metric_trend),
            )
        )

    fault_rows: list[str] = []
    for row in comparison.get("fault_changes") or []:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "UNKNOWN")
        prev_count = int(row.get("previous_count", 0) or 0)
        curr_count = int(row.get("current_count", 0) or 0)
        diff = int(row.get("delta", 0) or 0)
        if diff == 0:
            continue
        if diff < 0:
            direction = f"improved by {abs(diff)}"
        else:
            direction = f"worse by {diff}"
        fault_rows.append(f"{code}: {prev_count} → {curr_count} ({direction})")

    better = sum(1 for m in metrics if m.trend == "improved")
    worse = sum(1 for m in metrics if m.trend == "regressed")
    stable = sum(1 for m in metrics if m.trend == "stable")
    headline = "Set-to-Set Comparison"
    summary = f"Compared with the previous valid set: {better} improved, {worse} regressed, {stable} stayed the same."
    return ComparisonViewModel(
        headline=headline,
        summary=summary,
        metrics=metrics,
        fault_rows=fault_rows[:6],
    )


def _resolve_path(raw: Any) -> Path | None:
    """
    Try to resolve a raw path value (string or Path) against:
      1. As-is (absolute or already correct relative)
      2. Relative to cwd()
      3. Relative to the repo root (two levels up from ui/)
    Returns the first existing non-empty file, or None.
    """
    if not raw:
        return None
    s = str(raw)
    candidates = [
        Path(s),
        Path.cwd() / s,
        Path(__file__).resolve().parents[1] / s,
    ]
    for p in candidates:
        try:
            p = p.resolve()
            if p.exists() and p.stat().st_size > 0:
                return p
        except Exception:
            continue
    return None


def _fallback_path(raw_candidates: list[Any]) -> Path | None:
    for raw in raw_candidates:
        if raw:
            return Path(str(raw))
    return None


def resolve_overlay_path(payload, analysis) -> Path | None:
    """
    Walk every known key where the pipeline writes an overlay path.
    Keys confirmed present from debug output:
      - analysis['overlay_path']                  (top-level)
      - analysis['artifacts_v1']['overlay_path']  (artifacts block)
      - payload['highlights']['...']              (payload block)
      - payload['artifact_refs']['...']           (payload block)
    """
    raw_candidates: list[Any] = []

    if isinstance(analysis, dict):
        # Top-level key — confirmed present
        raw_candidates.append(analysis.get("overlay_path"))
        # artifacts_v1 block — confirmed present
        arts = analysis.get("artifacts_v1") or {}
        raw_candidates += [
            arts.get("overlay_path"),
            arts.get("overlay_video"),
            arts.get("annotated_video"),
        ]
        # set_summary_v1 fallback
        raw_candidates.append(
            (analysis.get("set_summary_v1") or {}).get("overlay_path")
        )

    if isinstance(payload, dict):
        # highlights block
        hl = payload.get("highlights") or {}
        raw_candidates += [
            hl.get("overlay_path"),
            hl.get("overlay_video"),
        ]
        # artifact_refs block — confirmed present in payload
        ar = payload.get("artifact_refs") or {}
        raw_candidates += [
            ar.get("overlay_path"),
            ar.get("overlay_video"),
            ar.get("annotated_video"),
        ]

    for raw in raw_candidates:
        p = _resolve_path(raw)
        if p is not None:
            return p

    return _fallback_path(raw_candidates)
