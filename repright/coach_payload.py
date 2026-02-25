from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_float_or_none(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build_coach_payload(analysis: dict[str, Any], message: str = "", load_kg: float | None = None) -> dict[str, Any]:
    reps = analysis.get("reps", [])
    rep_table = []
    for rep in reps:
        biomech = rep.get("biomech_v1") if isinstance(rep.get("biomech_v1"), dict) else {}
        faults = rep.get("faults_v1") if isinstance(rep.get("faults_v1"), list) else []
        rep_table.append(
            {
                "rep_index": int(rep.get("rep_index", 0)),
                "rom": _as_float_or_none(rep.get("rom")),
                "duration_sec": _as_float_or_none(rep.get("duration_sec")),
                "tempo_up_sec": _as_float_or_none(rep.get("tempo_up_sec")),
                "tempo_down_sec": _as_float_or_none(rep.get("tempo_down_sec")),
                "confidence": rep.get("confidence_v1") if isinstance(rep.get("confidence_v1"), dict) else {"level": "low", "reasons": ["missing_confidence"]},
                "tempo_down_inferred": bool(rep.get("tempo_down_inferred", False)),
                "end_frame_source": rep.get("end_frame_source"),
                "elbow_rom_deg": _as_float_or_none(biomech.get("elbow_rom_deg")),
                "faults": faults,
            }
        )

    fast_eccentric_reps = sum(1 for r in rep_table if (r["tempo_down_sec"] is not None and r["tempo_down_sec"] < 0.2))
    asym_rom_elbow_reps = sum(1 for r in rep_table if (r["elbow_rom_deg"] is not None and r["elbow_rom_deg"] < 35.0))
    tempo_vals = [r["tempo_down_sec"] for r in rep_table if r["tempo_down_sec"] is not None]
    artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}

    highlights = {
        "n_reps": int(analysis.get("set_summary_v1", {}).get("n_reps", len(reps))),
        "fast_eccentric_reps": fast_eccentric_reps,
        "asym_rom_elbow_reps": asym_rom_elbow_reps,
        "tempo_down_sec_min": min(tempo_vals) if tempo_vals else None,
        "tempo_down_sec_max": max(tempo_vals) if tempo_vals else None,
        "overlay_path": artifacts.get("overlay_path"),
        "metrics_path": artifacts.get("metrics_path"),
    }

    return {
        "schema_version": "coach_payload_v1",
        "user_message": message if message is not None else "",
        "exercise": analysis.get("exercise", "unknown"),
        "load_kg": load_kg,
        "analysis_v1": analysis,
        "highlights": highlights,
        "rep_table": rep_table,
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
