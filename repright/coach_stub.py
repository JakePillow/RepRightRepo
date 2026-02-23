from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _load(p: Path) -> Dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def _fmt_fault_counts(rep_table: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for r in rep_table:
        for f in (r.get("faults") or []):
            code = str(f.get("code") or "")
            if not code:
                continue
            counts[code] = counts.get(code, 0) + 1
    return counts


def coach_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    ex = payload.get("exercise") or "exercise"
    load = payload.get("load_kg")
    msg = payload.get("user_message") or ""

    highlights = payload.get("highlights") or {}
    n_reps = highlights.get("n_reps")
    td_min = highlights.get("tempo_down_sec_min")
    td_max = highlights.get("tempo_down_sec_max")

    rep_table = payload.get("rep_table") or []
    counts = _fmt_fault_counts(rep_table)

    # Super simple heuristic phrasing (placeholder for LLM)
    lines = []
    if load:
        lines.append(f"Bench @ {load:.0f}kg — quick take based on this set.")
    else:
        lines.append(f"{ex.title()} — quick take based on this set.")

    if n_reps is not None:
        lines.append(f"- Reps detected: {n_reps}")

    if td_min is not None and td_max is not None:
        lines.append(f"- Eccentric speed range: {td_min:.2f}s to {td_max:.2f}s (some reps very fast down)")

    if counts:
        top = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        top_str = ", ".join([f"{k}×{v}" for k, v in top[:5]])
        lines.append(f"- Flags seen: {top_str}")

    lines.append("")
    lines.append("Suggestions (stub):")
    if counts.get("TEMPO_FAST_ECCENTRIC", 0) > 0:
        lines.append("- Control the descent: aim for a slower eccentric (e.g., ~0.5–1.0s down) for consistency.")
    if counts.get("ASYM_ROM_ELBOW", 0) > 0:
        lines.append("- Left/right ROM looks uneven: check grip symmetry and bar path; film from the front once.")
    lines.append("- If you want, tell me your goal (strength vs hypertrophy) and I’ll tailor cues.")

    return {
        "schema_version": "coach_response_v1",
        "input_message": msg,
        "text": "\n".join(lines),
        "debug": {
            "fault_counts": counts,
            "highlights": highlights,
        },
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Coach stub: payload -> response JSON.")
    ap.add_argument("--payload", required=True, help="Path to coach_payload_v1 JSON")
    ap.add_argument("--out", required=True, help="Path to write coach response JSON")
    args = ap.parse_args()

    payload = _load(Path(args.payload))
    out = coach_response(payload)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(str(out_path).replace("\\", "/"))


if __name__ == "__main__":
    main()
