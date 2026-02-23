from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_json(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _rep_compact(rep: Dict[str, Any]) -> Dict[str, Any]:
    # Keep only what the coach needs (stable + explainable)
    biomech = rep.get("biomech_v1") or {}
    angles = (biomech.get("angles") or {})
    elbow = angles.get("elbow") or {}
    faults = rep.get("faults_v1") or []

    return {
        "rep_index": rep.get("rep_index"),
        "rom": _safe_float(rep.get("rom")),
        "duration_sec": _safe_float(rep.get("duration_sec")),
        "tempo_up_sec": _safe_float(rep.get("tempo_up_sec")),
        "tempo_down_sec": _safe_float(rep.get("tempo_down_sec")),
        "confidence": rep.get("confidence_v1") or {},
        "tempo_down_inferred": bool(rep.get("tempo_down_inferred", False)),
        "end_frame_source": rep.get("end_frame_source"),
        "elbow_rom_deg": _safe_float(elbow.get("rom_deg")),
        "faults": [
            {
                "code": f.get("code"),
                "severity": f.get("severity"),
                "value": f.get("value"),
                "threshold": f.get("threshold"),
                "evidence": f.get("evidence"),
            }
            for f in faults
        ],
    }


def _highlights(analysis: Dict[str, Any]) -> Dict[str, Any]:
    reps: List[Dict[str, Any]] = analysis.get("reps") or []
    n = len(reps)

    # Aggregate a few useful things without “tuning”
    tempo_down = [_safe_float(r.get("tempo_down_sec")) for r in reps]
    tempo_down = [t for t in tempo_down if t is not None]

    fast_ecc = 0
    asym_elbow = 0
    for r in reps:
        for f in (r.get("faults_v1") or []):
            if f.get("code") == "TEMPO_FAST_ECCENTRIC":
                fast_ecc += 1
            if f.get("code") == "ASYM_ROM_ELBOW":
                asym_elbow += 1

    return {
        "n_reps": n,
        "fast_eccentric_reps": fast_ecc,
        "asym_rom_elbow_reps": asym_elbow,
        "tempo_down_sec_min": min(tempo_down) if tempo_down else None,
        "tempo_down_sec_max": max(tempo_down) if tempo_down else None,
        "overlay_path": analysis.get("overlay_path"),
        "metrics_path": analysis.get("metrics_path"),
    }


@dataclass
class CoachPayloadBuilder:
    def build(
        self,
        analyzer_json_path: Path,
        user_message: str,
        load_kg: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        analysis = _load_json(Path(analyzer_json_path))

        reps = analysis.get("reps") or []
        payload: Dict[str, Any] = {
            "schema_version": "coach_payload_v1",
            "user_message": user_message,
            "exercise": analysis.get("exercise"),
            "load_kg": load_kg,
            "analysis_v1": analysis,               # full context for the model
            "highlights": _highlights(analysis),   # small summary for prompting
            "rep_table": [_rep_compact(r) for r in reps],  # compact per-rep table
        }
        if extra:
            payload["extra"] = extra
        return payload


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Build LLM coach payload from analyzer output.")
    ap.add_argument("--analyzer-json", required=True, help="Path to analyzer output JSON (e.g. _out/last_analyzer.json)")
    ap.add_argument("--message", required=True, help="User message (e.g., 'I did bench 80kg, how is my form?')")
    ap.add_argument("--load-kg", type=float, default=None, help="Optional load in kg")
    ap.add_argument("--out", required=True, help="Output JSON path")
    args = ap.parse_args()

    builder = CoachPayloadBuilder()
    payload = builder.build(
        analyzer_json_path=Path(args.analyzer_json),
        user_message=args.message,
        load_kg=args.load_kg,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(str(out_path).replace("\\", "/"))


if __name__ == "__main__":
    main()
