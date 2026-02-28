from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FAULT_CUES = {
    "LOW_ROM": "Use a fuller range while keeping shoulder position stable.",
    "RUSHED_CONCENTRIC": "Drive up smoothly; avoid bouncing or jerking.",
    "LUMBAR_FLEXION": "Brace harder and keep a neutral trunk throughout.",
}


def _safe_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _fmt_num(v: Any, fallback: str = "n/a") -> str:
    return f"{float(v):.2f}" if isinstance(v, (int, float)) else fallback


def run_coach(payload: dict[str, Any], mode: str = "stub") -> dict[str, Any]:
    payload = _safe_dict(payload)
    rep_table = _safe_list(payload.get("rep_table"))
    summary = _safe_dict(payload.get("high_level_summary"))
    patterns = _safe_dict(payload.get("form_pattern_aggregates"))
    user_message = str(payload.get("user_message") or "").strip()

    n_reps = int(summary.get("n_reps", len(rep_table)))
    exercise = str(summary.get("exercise") or payload.get("exercise") or "lift")

    fault_counts: dict[str, int] = {}
    for rep in rep_table:
        for fault in _safe_list(_safe_dict(rep).get("faults_v1")):
            code = str(_safe_dict(fault).get("code") or "").upper()
            if code:
                fault_counts[code] = fault_counts.get(code, 0) + 1

    top_faults = sorted(fault_counts.items(), key=lambda kv: kv[1], reverse=True)
    avg_rom = summary.get("avg_rom")
    tempo_down_avg = _safe_dict(summary.get("tempo_summary")).get("tempo_down_sec_avg")
    rom_std = patterns.get("rom_consistency_stddev")

    opening = f"You completed {n_reps} {exercise} rep(s)."
    if isinstance(avg_rom, (int, float)):
        opening += f" Avg ROM was {_fmt_num(avg_rom)}"
    if isinstance(tempo_down_avg, (int, float)):
        opening += f" with eccentric tempo ~{_fmt_num(tempo_down_avg)}s."

    note_line = f"You said: \"{user_message}\"." if user_message else "No extra note was provided for this set."

    cues: list[str] = []
    if top_faults:
        for code, _count in top_faults[:2]:
            cues.append(FAULT_CUES.get(code, f"Improve {code.lower().replace('_', ' ')} consistency."))
    else:
        cues.append("No major fault flags were detected; focus on repeatable setup and bracing each rep.")

    if isinstance(rom_std, (int, float)):
        cues.append(
            "Keep ROM consistent from rep to rep."
            if rom_std > 0.08
            else "ROM consistency looked solid; keep that same depth next set."
        )

    if isinstance(tempo_down_avg, (int, float)):
        if tempo_down_avg < 0.35:
            cues.append("Slow the lowering phase slightly to improve control and bar path.")
        else:
            cues.append("Maintain your current controlled lowering tempo on the next set.")

    cues = cues[:4]
    if len(cues) < 2:
        cues.append("Use the same stance/grip and breathing pattern for the next set.")

    follow_up = ""
    if top_faults:
        follow_up = "Optional: did any specific rep feel less stable than the others?"

    safety = ""
    if "pain" in user_message.lower() or "hurt" in user_message.lower():
        safety = "If pain is sharp or worsening, stop and seek a qualified medical professional."

    bullet_block = "\n".join([f"- {c}" for c in cues])
    response_text = f"{opening}\n{note_line}\n\n{bullet_block}"
    if safety:
        response_text += f"\n\n{safety}"
    if follow_up:
        response_text += f"\n\n{follow_up}"

    return {
        "schema_version": "coach_response_v1",
        "mode": mode,
        "response_text": response_text,
        "debug": {
            "n_reps": n_reps,
            "faults_present": [k for k, _v in top_faults],
            "system_contract": [
                "mention rep count + concrete metrics",
                "address user note",
                "2-4 actionable cues",
                "optional 1 follow-up question",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    response = run_coach(payload, mode="stub")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(response["response_text"])
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
