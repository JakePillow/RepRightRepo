from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple


DEFAULT_MODEL = os.getenv("REPRIGHT_COACH_MODEL", "gpt-5.4-mini")
DEFAULT_TIMEOUT = float(os.getenv("REPRIGHT_COACH_TIMEOUT_S", "30"))
MAX_RETRIES = int(os.getenv("REPRIGHT_COACH_MAX_RETRIES", "4"))
BASE_BACKOFF_S = float(os.getenv("REPRIGHT_COACH_BACKOFF_S", "1.2"))

# Bound prompt size / safety
MAX_HISTORY_TURNS = int(os.getenv("REPRIGHT_COACH_MAX_HISTORY_TURNS", "12"))
MAX_REP_ROWS = int(os.getenv("REPRIGHT_COACH_MAX_REP_ROWS", "12"))


def _safe_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _round_float(value: Any, digits: int = 2) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    return round(float(value), digits)


def _clean_comparison_context(raw: Any) -> dict[str, Any] | None:
    comparison = _safe_dict(raw)
    if not comparison:
        return None
    delta = _safe_dict(comparison.get("delta"))
    if not any(isinstance(v, (int, float)) for v in delta.values()):
        return None
    return comparison


def _round_long_decimals_in_text(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        try:
            value = float(token)
        except Exception:
            return token
        rounded = round(value, 2)
        return f"{rounded:.2f}".rstrip("0").rstrip(".")

    return re.sub(r"(?<![\w-])\d+\.\d{3,}(?![\w-])", repl, text)


def _sanitize_generated_line(text: str, *, n_reps: int | None, kind: str) -> str | None:
    line = " ".join(str(text or "").split()).strip()
    if not line:
        return None

    lower = line.lower()
    forbidden = (
        "comparison_v1",
        "driver_side",
        "driver_right",
        "driver_left",
        "rep_table",
        "confidence_v1",
        "faults_v1",
    )
    if any(token in lower for token in forbidden):
        return None

    if "0 faults recorded" in lower or "no numeric technique issue detected" in lower:
        return None

    if (n_reps or 0) <= 1 and ("stddev" in lower or "standard deviation" in lower or "consistency" in lower):
        return None

    if kind == "cue":
        line = line.replace("right-side driver signal", "same curl path")
        line = line.replace("driver signal", "movement path")

    line = _round_long_decimals_in_text(line)
    return line


def _sanitize_structured_feedback(structured: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(structured)
    summary = _safe_dict(payload.get("high_level_summary"))
    if not summary:
        summary = _safe_dict(_safe_dict(payload.get("analysis_v1")).get("set_summary_v1"))

    n_reps_raw = summary.get("n_reps")
    n_reps = int(round(float(n_reps_raw))) if isinstance(n_reps_raw, (int, float)) else None

    issues = []
    for item in _safe_list(cleaned.get("issues")):
        cooked = _sanitize_generated_line(str(item), n_reps=n_reps, kind="issue")
        if cooked:
            issues.append(cooked)
    cleaned["issues"] = issues[:5]

    cues = []
    for item in _safe_list(cleaned.get("cues")):
        cooked = _sanitize_generated_line(str(item), n_reps=n_reps, kind="cue")
        if cooked:
            cues.append(cooked)
    cleaned["cues"] = cues[:5]

    summary_text = str(cleaned.get("summary_text") or "").strip()
    if summary_text:
        cooked_summary = _sanitize_generated_line(summary_text, n_reps=n_reps, kind="summary")
        cleaned["summary_text"] = cooked_summary or ""
    else:
        cleaned["summary_text"] = ""

    return cleaned


def _stub_response(payload: dict, reason: str | None = None, status_code: int | None = None) -> Dict[str, Any]:
    exercise = payload.get("exercise")
    user_message = payload.get("user_message") or ""
    load_kg = payload.get("load_kg")
    analysis = payload.get("analysis_v1") if isinstance(payload.get("analysis_v1"), dict) else {}
    summary = _safe_dict(_safe_dict(analysis).get("set_summary_v1"))
    n_reps = summary.get("n_reps")
    comparison = _safe_dict(payload.get("comparison_v1"))

    load_line = f"Load provided: {float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "Load provided: none"
    comparison_line = ""
    if comparison:
        delta = _safe_dict(comparison.get("delta"))
        quality_delta = delta.get("quality_score")
        rom_delta = delta.get("avg_rom")
        comparison_line = (
            f"\nComparison to previous set: "
            f"quality delta={quality_delta}, avg ROM delta={rom_delta}."
        )

    text = f"""
    Coach summary for {exercise}:

    Reps detected: {n_reps}
    {load_line}
    {comparison_line}

    User note: {user_message}

    Focus on:
- Controlled tempo
- Consistent range of motion
- Stable bar path
""".strip()

    dbg: dict[str, Any] = {"provider": "stub", "fallback_reason": reason}
    if status_code is not None:
        dbg["status_code"] = int(status_code)

    return {
        "mode": "stub",
        "response_text": text,
        "structured": {},
        "debug": dbg,
    }


def _compact_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for h in history[-MAX_HISTORY_TURNS:]:
        if isinstance(h, dict):
            role = str(h.get("role") or "user")
            content = h.get("content")
            if content is None:
                content = h.get("user") or h.get("assistant") or ""
            out.append({"role": role, "content": str(content)[:700]})
    return out


def _compact_rep_table(rep_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rep_table[:MAX_REP_ROWS]:
        if not isinstance(r, dict):
            continue
        conf = _safe_dict(r.get("confidence_v1"))
        faults = _safe_list(r.get("faults_v1"))
        out.append(
            {
                "rep_index": r.get("rep_index"),
                "rom": _round_float(r.get("rom")),
                "duration_sec": _round_float(r.get("duration_sec")),
                "tempo_down_sec": _round_float(r.get("tempo_down_sec")),
                "tempo_up_sec": _round_float(r.get("tempo_up_sec")),
                "confidence_level": conf.get("level"),
                "faults_v1": [
                    {
                        "code": _safe_dict(f).get("code") or "UNKNOWN",
                        "severity": _safe_dict(f).get("severity") or "info",
                        "value": _round_float(_safe_dict(f).get("value"), 3)
                        if isinstance(_safe_dict(f).get("value"), (int, float))
                        else _safe_dict(f).get("value"),
                        "threshold": _round_float(_safe_dict(f).get("threshold"), 3)
                        if isinstance(_safe_dict(f).get("threshold"), (int, float))
                        else _safe_dict(f).get("threshold"),
                    }
                    for f in faults[:10]
                    if isinstance(f, dict)
                ],
            }
        )
    return out


def _sleep_backoff(attempt: int, retry_after_s: float | None) -> None:
    if retry_after_s is not None and retry_after_s > 0:
        time.sleep(retry_after_s)
        return
    base = BASE_BACKOFF_S * (2 ** max(0, attempt - 1))
    jitter = random.uniform(0.0, 0.25 * base)
    time.sleep(base + jitter)


def _parse_retry_after(err: urllib.error.HTTPError) -> float | None:
    try:
        ra = err.headers.get("Retry-After")
        if not ra:
            return None
        return float(ra)
    except Exception:
        return None


def _build_messages(payload: dict) -> list[dict[str, Any]]:
    """
    Build Responses API input messages.
    We keep it deterministic and data-grounded:
    - coach MUST cite numerical values
    - produce JSON structured output
    """
    analysis = _safe_dict(payload.get("analysis_v1"))
    summary = _safe_dict(payload.get("high_level_summary"))
    aggregates = _safe_dict(payload.get("form_pattern_aggregates"))

    history = _compact_history(_safe_list(payload.get("history")))
    rep_table = _compact_rep_table(_safe_list(payload.get("rep_table")))

    user_message = str(payload.get("user_message") or "")
    exercise = str(payload.get("exercise") or analysis.get("exercise") or "unknown")
    load_kg = payload.get("load_kg")

    # Provide compact "facts" object that the model must ground on
    comparison = _clean_comparison_context(payload.get("comparison_v1"))

    facts = {
        "exercise": exercise,
        "load_kg": _round_float(load_kg, 1) if isinstance(load_kg, (int, float)) else None,
        "user_message": user_message,
        "summary": summary or _safe_dict(analysis.get("set_summary_v1")),
        "rep_table": rep_table,
        "aggregates": aggregates,
        "comparison_v1": comparison,
        "repeated_faults": _safe_list(aggregates.get("repeated_faults")),
        "history": history,
    }

    system = (
        "You are RepRight, an elite strength coach.\n"
        "Hard rules:\n"
        "- Base ALL claims strictly on the numeric data provided in FACTS.\n"
        "- Never invent values.\n"
        "- Sound like a premium personal trainer in chat: direct, calm, specific, and supportive.\n"
        "- Lead with the most useful takeaway first.\n"
        "- Prefer plain coaching language over lab-report language.\n"
        "- Keep sentences tight and readable.\n"
        "- When you mention a metric, include the number and unit where relevant.\n"
        "- Round decimals to at most 2 places unless a threshold needs 3 places.\n"
        "- If FACTS.load_kg is a number, treat the load as provided and do not say weight is missing.\n"
        "- If FACTS.comparison_v1 is null, do not mention comparison at all.\n"
        "- If FACTS.comparison_v1 is present, compare the current set against the previous set first and ground claims in the deltas.\n"
        "- Never mention internal field names or JSON keys such as comparison_v1, rep_table, driver_signal, driver_side, confidence_v1, or faults_v1.\n"
        "- If there are no faults, say the set looks clean instead of inventing an issue.\n"
        "- If there is only one rep, do not discuss consistency or standard deviation beyond saying more reps are needed to judge consistency.\n"
        "- If data is insufficient, say what is missing.\n"
        "- Output MUST follow the JSON schema exactly.\n"
    )

    user = (
        "FACTS (authoritative JSON; use ONLY this):\n"
        + json.dumps(facts, ensure_ascii=False)
        + "\n\n"
        "Task:\n"
        "1) Identify up to 3 meaningful findings using numeric evidence; if the set is clean, findings may be positive or cautionary rather than faults.\n"
        "2) If comparison_v1 exists, explain what improved, regressed, or stayed similar using numeric deltas.\n"
        "3) Give 2 actionable cues written as short commands.\n"
        "4) Give an overall_score 0-100 grounded on consistency + faults.\n"
        "5) If load_kg is present, you may reference it directly, but do not invent progression advice that requires missing context such as RPE, bodyweight, or training history.\n"
        "6) summary_text: 2 to 4 sentences, under 90 words, opening with a clear coaching verdict. Make it sound like a sharp AI personal trainer, not a report. Reference only the numbers that actually matter. If the user gave a goal or note, address it when relevant.\n"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _call_openai(messages: list[dict[str, Any]]) -> Tuple[dict[str, Any], dict[str, Any]]:
    """
    Calls OpenAI Chat Completions API using urllib (no SDK dependency).
    Returns: (response_json, debug_raw)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing_openai_api_key")

    body = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "coach_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
                        "issues": {"type": "array", "items": {"type": "string"}, "minItems": 0, "maxItems": 5},
                        "cues": {"type": "array", "items": {"type": "string"}, "minItems": 0, "maxItems": 5},
                        "summary_text": {"type": "string"},
                    },
                    "required": ["overall_score", "issues", "cues", "summary_text"],
                    "additionalProperties": False,
                },
            }
        },
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)

    dbg = {"response_id": data.get("id"), "model": data.get("model")}
    return data, dbg


def _extract_structured_from_responses_api(resp_json: dict[str, Any]) -> dict[str, Any]:
    """
    Chat Completions API returns:
      resp_json["choices"][0]["message"]["content"]  (string)
    With json_schema response_format, that string is JSON.
    """
    choices = _safe_list(resp_json.get("choices"))
    if not choices:
        raise RuntimeError("openai_parse_error: missing_choices")

    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue
        txt = message.get("content")
        if isinstance(txt, str) and txt.strip():
            try:
                return json.loads(txt)
            except Exception as e:
                raise RuntimeError(f"openai_parse_error: invalid_json_text ({e})")
    raise RuntimeError("openai_parse_error: no_message_content_found")


def _metric_lines(payload: dict[str, Any], structured: dict[str, Any]) -> list[str]:
    analysis = _safe_dict(payload.get("analysis_v1"))
    summary = _safe_dict(payload.get("high_level_summary"))
    if not summary:
        summary = _safe_dict(analysis.get("set_summary_v1"))

    lines: list[str] = []
    score = structured.get("overall_score")
    if isinstance(score, (int, float)):
        lines.append(f"Quality score: {round(float(score), 1)}/100")

    load_kg = payload.get("load_kg")
    if isinstance(load_kg, (int, float)):
        lines.append(f"Load: {float(load_kg):.1f} kg")

    n_reps = summary.get("n_reps")
    if isinstance(n_reps, (int, float)):
        lines.append(f"Reps: {int(round(float(n_reps)))}")

    avg_rom = summary.get("avg_rom")
    if isinstance(avg_rom, (int, float)):
        lines.append(f"Average ROM: {float(avg_rom):.2f}")

    avg_duration = summary.get("avg_duration_sec")
    if isinstance(avg_duration, (int, float)):
        lines.append(f"Average rep duration: {float(avg_duration):.2f} s")

    avg_tempo_up = summary.get("tempo_summary", {}).get("tempo_up_sec_avg") if isinstance(summary.get("tempo_summary"), dict) else summary.get("avg_tempo_up_sec")
    if not isinstance(avg_tempo_up, (int, float)):
        avg_tempo_up = summary.get("avg_tempo_up_sec")
    if isinstance(avg_tempo_up, (int, float)):
        lines.append(f"Average lift phase: {float(avg_tempo_up):.2f} s")

    avg_tempo_down = summary.get("tempo_summary", {}).get("tempo_down_sec_avg") if isinstance(summary.get("tempo_summary"), dict) else summary.get("avg_tempo_down_sec")
    if not isinstance(avg_tempo_down, (int, float)):
        avg_tempo_down = summary.get("avg_tempo_down_sec")
    if isinstance(avg_tempo_down, (int, float)):
        lines.append(f"Average lowering phase: {float(avg_tempo_down):.2f} s")

    low_conf = summary.get("n_low_confidence")
    if isinstance(low_conf, (int, float)):
        lines.append(f"Low-confidence reps: {int(round(float(low_conf)))}")

    comparison = _clean_comparison_context(payload.get("comparison_v1"))
    if comparison:
        delta = _safe_dict(comparison.get("delta"))
        if isinstance(delta.get("quality_score"), (int, float)):
            lines.append(f"Quality delta vs previous set: {float(delta['quality_score']):+.1f}")
        if isinstance(delta.get("avg_rom"), (int, float)):
            lines.append(f"ROM delta vs previous set: {float(delta['avg_rom']):+.2f}")
        if isinstance(delta.get("load_kg"), (int, float)):
            lines.append(f"Load delta vs previous set: {float(delta['load_kg']):+.1f} kg")

    return lines


def _render_text(structured: dict[str, Any], payload: dict[str, Any]) -> str:
    score = structured.get("overall_score")
    issues = _safe_list(structured.get("issues"))
    cues = _safe_list(structured.get("cues"))
    summary = str(structured.get("summary_text") or "").strip()

    lines: list[str] = []
    if summary:
        lines.append(f"**Coach take:** {summary}")
    elif isinstance(score, (int, float)):
        lines.append(f"**Coach take:** This set scored {round(float(score), 1)}/100 and the overall pattern looks solid.")

    if issues:
        if lines:
            lines.append("")
        lines.append("**What stood out:**")
        for it in issues[:4]:
            lines.append(f"- {str(it)}")
    elif isinstance(score, (int, float)):
        if lines:
            lines.append("")
        lines.append("**What stood out:**")
        lines.append(f"- Overall lift quality came out at {round(float(score), 1)}/100 with no major technique faults flagged.")

    if cues:
        if lines:
            lines.append("")
        lines.append("**Next set cues:**")
        for c in cues[:4]:
            lines.append(f"- {str(c)}")

    metric_lines = _metric_lines(payload, structured)
    if metric_lines:
        if lines:
            lines.append("")
        lines.append("**Numbers I used:**")
        for item in metric_lines:
            lines.append(f"- {item}")

    return "\n".join(lines).strip()


def format_response_text(response: dict[str, Any] | None, payload: dict[str, Any] | None) -> str:
    if not isinstance(response, dict):
        return ""
    structured = _safe_dict(response.get("structured"))
    if structured:
        cleaned = _sanitize_structured_feedback(structured, _safe_dict(payload))
        return _render_text(cleaned, _safe_dict(payload))
    return str(response.get("response_text") or "").strip()


def run_coach(payload: dict, mode: str = "auto") -> Dict[str, Any]:
    """
    mode:
      auto -> use GPT if OPENAI_API_KEY exists, else stub
      gpt  -> force GPT (fallback to stub on error)
      stub -> always stub
    """
    mode = (mode or os.getenv("REPRIGHT_COACH_MODE", "auto")).lower().strip()

    if mode == "stub":
        return _stub_response(payload, reason="forced_stub")

    if mode == "auto" and not os.getenv("OPENAI_API_KEY"):
        return _stub_response(payload, reason="no_api_key")

    last_err: str | None = None
    last_status: int | None = None

    messages = _build_messages(payload)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.time()
            resp_json, raw_dbg = _call_openai(messages)
            structured = _extract_structured_from_responses_api(resp_json)
            structured = _sanitize_structured_feedback(structured, payload)
            text = _render_text(structured, payload)
            dt = time.time() - t0

            return {
                "mode": "gpt",
                "response_text": text,
                "structured": structured,
                "debug": {
                    "provider": "openai",
                    "model": DEFAULT_MODEL,
                    "latency_s": round(dt, 3),
                    **raw_dbg,
                },
            }

        except urllib.error.HTTPError as e:
            last_status = int(getattr(e, "code", 0) or 0)
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            last_err = f"HTTP Error {last_status}: {getattr(e, 'reason', '')}".strip()
            if body:
                # include a short slice (don't blow logs)
                last_err += f" | body={body[:400]}"

            if last_status in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                ra = _parse_retry_after(e)
                _sleep_backoff(attempt, ra)
                continue
            break

        except urllib.error.URLError as e:
            last_err = f"url_error: {e}"
            if attempt < MAX_RETRIES:
                _sleep_backoff(attempt, None)
                continue
            break

        except Exception as e:
            last_err = str(e)
            break

    return _stub_response(payload, reason=last_err, status_code=last_status)
