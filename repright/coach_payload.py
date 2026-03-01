from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import pstdev
from typing import Any


def _as_float_or_none(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _std(values: list[float | None]) -> float | None:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if len(nums) < 2:
        return 0.0 if nums else None
    return float(pstdev(nums))


def build_coach_payload(
    analysis: dict[str, Any],
    message: str = "",
    load_kg: float | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    # ---------- safety / normalization ----------
    analysis = _safe_dict(analysis)
    reps = _safe_list(analysis.get("reps"))
    set_summary = _safe_dict(analysis.get("set_summary_v1"))
    artifacts = _safe_dict(analysis.get("artifacts_v1"))

    # Bound history to keep prompts safe + deterministic
    hist = _safe_list(history) if history is not None else _safe_list(analysis.get("history"))
    hist = hist[-12:]  # last 12 turns max

    # Prefer canonical artifact paths (pipeline writes these)
    overlay_path = artifacts.get("overlay_path") or analysis.get("overlay_path")
    analysis_json = artifacts.get("analysis_json") or artifacts.get("metrics_path") or analysis.get("metrics_path")
    run_dir = artifacts.get("run_dir")

    rep_table: list[dict[str, Any]] = []
    fault_counter: Counter[str] = Counter()

    for rep in reps:
        rep_d = _safe_dict(rep)
        biomech = _safe_dict(rep_d.get("biomech_v1"))
        confidence = _safe_dict(rep_d.get("confidence_v1"))
        faults_raw = _safe_list(rep_d.get("faults_v1"))

        faults: list[dict[str, Any]] = []
        for f in faults_raw:
            fd = _safe_dict(f)
            code = str(fd.get("code") or "UNKNOWN")
            faults.append(
                {
                    "code": code,
                    "severity": str(fd.get("severity") or "info"),
                    "value": fd.get("value"),
                    "threshold": fd.get("threshold"),
                    "evidence": fd.get("evidence"),
                }
            )
            fault_counter[code] += 1

        rep_row = {
            "rep_index": int(rep_d.get("rep_index", len(rep_table) + 1)),
            "start_frame": rep_d.get("start_frame"),
            "peak_frame": rep_d.get("peak_frame"),
            "end_frame": rep_d.get("end_frame"),
            "duration_sec": _as_float_or_none(rep_d.get("duration_sec")),
            "tempo_up_sec": _as_float_or_none(rep_d.get("tempo_up_sec")),
            "tempo_down_sec": _as_float_or_none(rep_d.get("tempo_down_sec")),
            "tempo_up_inferred": bool(rep_d.get("tempo_up_inferred", False)),
            "tempo_down_inferred": bool(rep_d.get("tempo_down_inferred", False)),
            "rom": _as_float_or_none(rep_d.get("rom")),
            "confidence_v1": {
                "level": str(confidence.get("level") or "unknown"),
                "reasons": _safe_list(confidence.get("reasons")),
            },
            "faults_v1": faults,
            # keep these for debugging / inversions
            "driver_signal": rep_d.get("driver_signal") or analysis.get("driver_signal"),
            "inversion": rep_d.get("inversion") if "inversion" in rep_d else analysis.get("inversion"),
            "elbow_rom_deg": _as_float_or_none(biomech.get("elbow_rom_deg")),
        }
        rep_table.append(rep_row)

    # ---------- aggregates ----------
    rom_vals = [r.get("rom") for r in rep_table]
    dur_vals = [r.get("duration_sec") for r in rep_table]
    tempo_up_vals = [r.get("tempo_up_sec") for r in rep_table]
    tempo_down_vals = [r.get("tempo_down_sec") for r in rep_table]

    conf_rank = {"low": 0, "medium": 1, "high": 2}
    worst_rep = None
    if rep_table:
        worst_rep = min(
            rep_table,
            key=lambda r: (
                conf_rank.get(str(_safe_dict(r.get("confidence_v1")).get("level", "")).lower(), -1),
                -len(_safe_list(r.get("faults_v1"))),
            ),
        )

    repeated_faults = [{"code": code, "count": int(count)} for code, count in fault_counter.most_common()]

    # Prefer analysis.exercise but keep stable fallback
    exercise = str(analysis.get("exercise") or "unknown")

    high_level = {
        "exercise": exercise,
        "fps": analysis.get("fps"),
        "n_reps": int(set_summary.get("n_reps", len(rep_table))),
        "avg_rom": set_summary.get("avg_rom"),
        "avg_duration_sec": set_summary.get("avg_duration_sec"),
        "tempo_summary": {
            "tempo_up_sec_min": min((v for v in tempo_up_vals if isinstance(v, (int, float))), default=None),
            "tempo_up_sec_max": max((v for v in tempo_up_vals if isinstance(v, (int, float))), default=None),
            "tempo_up_sec_avg": set_summary.get("avg_tempo_up_sec"),
            "tempo_down_sec_min": min((v for v in tempo_down_vals if isinstance(v, (int, float))), default=None),
            "tempo_down_sec_max": max((v for v in tempo_down_vals if isinstance(v, (int, float))), default=None),
            "tempo_down_sec_avg": set_summary.get("avg_tempo_down_sec"),
        },
        "driver_signal": analysis.get("driver_signal"),
        "inversion": analysis.get("inversion"),
    }

    pattern_aggregates = {
        "repeated_faults": repeated_faults,
        "worst_rep": {
            "rep_index": (worst_rep or {}).get("rep_index"),
            "confidence": _safe_dict((worst_rep or {}).get("confidence_v1")).get("level"),
            "fault_count": len(_safe_list((worst_rep or {}).get("faults_v1"))),
        },
        "rom_consistency_stddev": _std(rom_vals),
        "tempo_up_consistency_stddev": _std(tempo_up_vals),
        "tempo_down_consistency_stddev": _std(tempo_down_vals),
        "duration_consistency_stddev": _std(dur_vals),
        "asymmetry": analysis.get("asymmetry") or set_summary.get("asymmetry"),
    }

    # Highlights are what UI should primarily use (and LLM can cite)
    highlights = {
        "n_reps": high_level["n_reps"],
        # always prefer artifact overlay first
        "overlay_path": overlay_path,
        "analysis_json": analysis_json,
        "run_dir": run_dir,
    }

    # Artifact refs (explicit)
    artifact_refs = {
        "overlay_path": overlay_path,
        "analysis_json": analysis_json,
        "run_dir": run_dir,
    }

    # IMPORTANT: keep analysis_v1 embedded (LLM needs full context; UI can reload)
    return {
        "schema_version": "coach_payload_v2",
        "user_message": message or "",
        "exercise": exercise,
        "load_kg": load_kg,
        "history": hist,
        "analysis_v1": analysis,
        "high_level_summary": high_level,
        "rep_table": rep_table,  # downstream will bound again if needed
        "form_pattern_aggregates": pattern_aggregates,
        "artifact_refs": artifact_refs,
        "highlights": highlights,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analyzer-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--message", default="")
    parser.add_argument("--load-kg", type=float, default=None)
    args = parser.parse_args()

    analysis = json.loads(Path(args.analyzer_json).read_text(encoding="utf-8"))
    payload = build_coach_payload(analysis, message=args.message, load_kg=args.load_kg)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
