from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


DEFAULT_MODEL = os.getenv("REPRIGHT_COACH_MODEL", "gpt-4.1-mini")
DEFAULT_TIMEOUT = float(os.getenv("REPRIGHT_COACH_TIMEOUT_S", "30"))
MAX_RETRIES = int(os.getenv("REPRIGHT_COACH_MAX_RETRIES", "4"))
BASE_BACKOFF_S = float(os.getenv("REPRIGHT_COACH_BACKOFF_S", "1.2"))

# Bound prompt size / safety
MAX_HISTORY_TURNS = int(os.getenv("REPRIGHT_COACH_MAX_HISTORY_TURNS", "12"))
MAX_REP_ROWS = int(os.getenv("REPRIGHT_COACH_MAX_REP_ROWS", "12"))


# ----------------------------
# Helpers
# ----------------------------
def _safe_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _stub_response(payload: dict, reason: str | None = None, status_code: int | None = None) -> Dict[str, Any]:
    exercise = payload.get("exercise")
    user_message = payload.get("user_message") or ""
    analysis = payload.get("analysis_v1") if isinstance(payload.get("analysis_v1"), dict) else {}
    summary = _safe_dict(_safe_dict(analysis).get("set_summary_v1"))
    n_reps = summary.get("n_reps")

    text = f"""
Coach summary for {exercise}:

Reps detected: {n_reps}

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
        "structured": {},  # keep key present for callers
        "debug": dbg,
    }


def _compact_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for h in history[-MAX_HISTORY_TURNS:]:
        if isinstance(h, dict):
            role = str(h.get("role") or "user")
            content = h.get("content")
            if content is None:
                # tolerate old shapes
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
                "rom": r.get("rom"),
                "duration_sec": r.get("duration_sec"),
                "tempo_down_sec": r.get("tempo_down_sec"),
                "tempo_up_sec": r.get("tempo_up_sec"),
                "confidence_level": conf.get("level"),
                "faults_v1": [
                    {
                        "code": _safe_dict(f).get("code") or "UNKNOWN",
                        "severity": _safe_dict(f).get("severity") or "info",
                        "value": _safe_dict(f).get("value"),
                        "threshold": _safe_dict(f).get("threshold"),
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


# ----------------------------
# Prompt + OpenAI call
# ----------------------------
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

    # Provide compact “facts” object that the model must ground on
    facts = {
        "exercise": exercise,
        "user_message": user_message,
        "summary": summary or _safe_dict(analysis.get("set_summary_v1")),
        "rep_table": rep_table,
        "aggregates": aggregates,
        "repeated_faults": _safe_list(aggregates.get("repeated_faults")),
        "artifact_refs": _safe_dict(payload.get("artifact_refs")),
        "history": history,
    }

    system = (
        "You are RepRight, an elite strength coach.\n"
        "Hard rules:\n"
        "- Base ALL claims strictly on the numeric data provided in FACTS.\n"
        "- Never invent values.\n"
        "- When you mention a metric, include the number (and threshold if provided).\n"
        "- If data is insufficient, say what is missing.\n"
        "- Output MUST follow the JSON schema exactly.\n"
    )

    # The user content is the *only* thing we want the model to use as data
    user = (
        "FACTS (authoritative JSON; use ONLY this):\n"
        + json.dumps(facts, ensure_ascii=False)
        + "\n\n"
        "Task:\n"
        "1) Identify up to 3 key issues using numeric evidence (rep_index + values).\n"
        "2) Give 2 actionable cues.\n"
        "3) Give an overall_score 0-100 grounded on consistency + faults.\n"
        "4) summary_text: a short natural paragraph (<120 words) referencing the numbers.\n"
    )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _call_openai(messages: list[dict[str, Any]]) -> Tuple[dict[str, Any], dict[str, Any]]:
    """
    Calls OpenAI Responses API using urllib (no SDK dependency).
    Returns: (response_json, debug_raw)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing_openai_api_key")

    # Responses API expects `input` as either a string or list of messages.
    # Structured output is controlled via `text.format`.
    body = {
        "model": DEFAULT_MODEL,
        "input": messages,
        "text": {
            "format": {
                "type": "json_schema",
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
        "https://api.openai.com/v1/responses",
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
    Responses API typically returns:
      resp_json["output"][0]["content"][0]["text"]  (string)
    With json_schema format, that string should be JSON.
    """
    out = _safe_list(resp_json.get("output"))
    if not out:
        raise RuntimeError("openai_parse_error: missing_output")

    # Find first message block with output_text
    for block in out:
        if not isinstance(block, dict):
            continue
        content = _safe_list(block.get("content"))
        for c in content:
            if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                txt = c.get("text")
                if isinstance(txt, str) and txt.strip():
                    try:
                        return json.loads(txt)
                    except Exception as e:
                        raise RuntimeError(f"openai_parse_error: invalid_json_text ({e})")
    raise RuntimeError("openai_parse_error: no_output_text_found")


def _render_text(structured: dict[str, Any]) -> str:
    """
    Convert structured JSON into a nice human response.
    (UI can show this; we still return structured for scoring widgets etc.)
    """
    score = structured.get("overall_score")
    issues = _safe_list(structured.get("issues"))
    cues = _safe_list(structured.get("cues"))
    summary = structured.get("summary_text") or ""

    lines: list[str] = []
    if isinstance(score, (int, float)):
        lines.append(f"**Lift quality:** {round(float(score), 1)}/100")
        lines.append("")

    if issues:
        lines.append("**Key issues (evidence-based):**")
        for it in issues[:5]:
            lines.append(f"- {str(it)}")
        lines.append("")

    if cues:
        lines.append("**Cues:**")
        for c in cues[:5]:
            lines.append(f"- {str(c)}")
        lines.append("")

    if isinstance(summary, str) and summary.strip():
        lines.append(str(summary).strip())

    return "\n".join(lines).strip()


# ----------------------------
# Public API
# ----------------------------
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

    # Build once (deterministic)
    messages = _build_messages(payload)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.time()
            resp_json, raw_dbg = _call_openai(messages)
            structured = _extract_structured_from_responses_api(resp_json)
            text = _render_text(structured)
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
            # read server body for real diagnostics
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            last_err = f"HTTP Error {last_status}: {getattr(e, 'reason', '')}".strip()
            if body:
                # include a short slice (don’t blow logs)
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