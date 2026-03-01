from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request


FAULT_CUES = {
    "LOW_ROM": "Use a fuller range while keeping shoulder position stable.",
    "RUSHED_CONCENTRIC": "Drive up smoothly; avoid bouncing or jerking.",
    "LUMBAR_FLEXION": "Brace harder and keep a neutral trunk throughout.",
}

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"

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


def _compact_payload_for_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    rep_table = _safe_list(payload.get("rep_table"))[:8]
    slim_reps: list[dict[str, Any]] = []
    for rep in rep_table:
        r = _safe_dict(rep)
        slim_reps.append(
            {
                "rep_index": r.get("rep_index"),
                "duration_sec": r.get("duration_sec"),
                "tempo_up_sec": r.get("tempo_up_sec"),
                "tempo_down_sec": r.get("tempo_down_sec"),
                "rom": r.get("rom"),
                "confidence_v1": r.get("confidence_v1"),
                "faults_v1": r.get("faults_v1"),
            }
        )

    return {
        "exercise": payload.get("exercise"),
        "user_message": payload.get("user_message"),
        "load_kg": payload.get("load_kg"),
        "high_level_summary": payload.get("high_level_summary"),
        "form_pattern_aggregates": payload.get("form_pattern_aggregates"),
        "artifact_refs": payload.get("artifact_refs"),
        "history": _safe_list(payload.get("history"))[-6:],
        "rep_table": slim_reps,
    }


def _gpt_coach_response(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = os.getenv("REPRIGHT_COACH_MODEL", "gpt-4.1-mini")
    timeout_s = float(os.getenv("REPRIGHT_COACH_TIMEOUT_S", "30"))

    system_instruction = (
        "You are RepRight Coach. Use only provided metrics. "
        "Output concise coaching with this exact structure:\n"
        "1) One-sentence set summary with reps count and at least 1 concrete metric.\n"
        "2) Address the user's note directly in one sentence.\n"
        "3) 3 bullet cues: technique / tempo / next set.\n"
        "4) Include a safety disclaimer only when pain/injury is implied.\n"
        "5) Optional: one follow-up question at most."
    )

    user_payload = _compact_payload_for_prompt(payload)
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "text", "text": system_instruction}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Coach this set based on the JSON payload below. Be concrete and data-driven.\n"
                        + json.dumps(user_payload, ensure_ascii=False),
                    }
                ],
            },
        ],
    }

    req = request.Request(
        OPENAI_RESPONSES_URL,
        method="POST",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)

    output_text = data.get("output_text")
    if not output_text:
        output_text = "I could not generate a coaching response from the model output."

    return {
        "schema_version": "coach_response_v1",
        "mode": mode,
        "response_text": output_text,
        "debug": {
            "provider": "openai",
            "model": model,
            "response_id": data.get("id"),
        },
    }


def run_coach(payload: dict[str, Any], mode: str = "auto") -> dict[str, Any]:
    payload = _safe_dict(payload)
    requested = (mode or "auto").lower().strip()

    if requested == "stub":
        return _build_stub_response(payload, mode="stub")

    env_mode = os.getenv("REPRIGHT_COACH_MODE", "auto").lower().strip()
    use_gpt = requested == "gpt" or env_mode == "gpt"

    if not use_gpt:
        # auto mode: use GPT if key exists, else stub
        use_gpt = bool(os.getenv("OPENAI_API_KEY"))

    if use_gpt:
        try:
            return _gpt_coach_response(payload, mode="gpt")
        except (RuntimeError, error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
            fallback = _build_stub_response(payload, mode="stub_fallback")
            fallback.setdefault("debug", {})
            fallback["debug"].update(
                {
                    "fallback_reason": str(exc),
                    "requested_mode": requested,
                    "env_mode": env_mode,
                }
            )
            return fallback

    return _build_stub_response(payload, mode="stub")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--mode", default="auto", choices=["auto", "stub", "gpt"])
    args = parser.parse_args()

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    response = run_coach(payload, mode=args.mode)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(response["response_text"])
    print(f"[OK] wrote {out}")


if __name__ == "__main__":
    main()
