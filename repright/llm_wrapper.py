from __future__ import annotations

import json
import os
import random
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple, Optional


DEFAULT_MODEL = os.getenv("REPRIGHT_COACH_MODEL", "gpt-4.1-mini")
DEFAULT_TIMEOUT = float(os.getenv("REPRIGHT_COACH_TIMEOUT_S", "30"))
MAX_RETRIES = int(os.getenv("REPRIGHT_COACH_MAX_RETRIES", "4"))
BASE_BACKOFF_S = float(os.getenv("REPRIGHT_COACH_BACKOFF_S", "1.2"))

# Bound prompt size / safety
MAX_HISTORY_TURNS = int(os.getenv("REPRIGHT_COACH_MAX_HISTORY_TURNS", "12"))
MAX_REP_ROWS = int(os.getenv("REPRIGHT_COACH_MAX_REP_ROWS", "12"))


def _stub_response(payload: dict, reason: str | None = None, status_code: int | None = None) -> Dict[str, Any]:
    exercise = payload.get("exercise")
    user_message = payload.get("user_message") or ""
    summary = (payload.get("analysis_v1") or {}).get("set_summary_v1", {}) if isinstance(payload.get("analysis_v1"), dict) else {}
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

    return {"mode": "stub", "response_text": text, "debug": dbg}


def _safe_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _safe_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _compact_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Expect [{role, content}] but tolerate old shapes
    out: list[dict[str, Any]] = []
    for h in history[-MAX_HISTORY_TURNS:]:
        if isinstance(h, dict):
            role = h.get("role") or ("user" if "user" in h else "assistant")
            content = h.get("content") or h.get("user") or h.get("assistant") or ""
            out.append({"role": str(role), "content": str(content)[:600]})
    return out


def _compact_rep_table(rep_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Keep numerics + faults; drop noise
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
                "fault_codes": [(_safe_dict(f).get("code") or "UNKNOWN") for f in faults][:8],
                # include thresholded numeric evidence when present
                "faults_v1": [
                    {
                        "code": _safe_dict(f).get("code"),
                        "severity": _safe_dict(f).get("severity"),
                        "value": _safe_dict(f).get("value"),
                        "threshold": _safe_dict(f).get("threshold"),
                    }
                    for f in faults[:8]
                ],
            }
        )
    return out


def _build_prompt(payload: dict) -> str:
    """
    Deterministic prompt contract:
    - MUST ground advice in provided numeric values (ROM/tempo/duration/fault thresholds)
    - MUST cite at least 3 numbers when n_reps > 0
    - MUST avoid inventing any measurement not in JSON
    """
    payload = _safe_dict(payload)

    analysis = _safe_dict(payload.get("analysis_v1"))
    high = _safe_dict(payload.get("high_level_summary"))
    reps = _safe_list(payload.get("rep_table"))  # prefer rep_table (already normalized)
    aggs = _safe_dict(payload.get("form_pattern_aggregates"))
    artifact_refs = _safe_dict(payload.get("artifact_refs"))
    history = _safe_list(payload.get("history"))

    prompt_obj = {
        "developer_instructions": [
            "You are RepRight, an elite strength coach and biomechanics assistant.",
            "Only use the JSON values provided. Do NOT invent data.",
            "Ground feedback in the numeric fields (ROM, tempo, duration, thresholds, fault counts).",
            "If n_reps > 0: cite at least 3 specific numbers from the payload (e.g., avg_rom, tempo_down_sec_avg, rep 2 rom).",
            "If you give a cue (instruction), include the numeric reason in the same bullet.",
            "Output should be concise and directly actionable.",
            "Structure the response as: (1) One-line verdict, (2) 2–4 bullets of key findings with numbers, (3) 2–4 cues with numeric justification, (4) one follow-up question.",
        ],
        "context": {
            "exercise": payload.get("exercise") or high.get("exercise") or analysis.get("exercise"),
            "user_message": payload.get("user_message") or "",
            "load_kg": payload.get("load_kg"),
            "high_level_summary": high,
            "rep_table": _compact_rep_table(reps),
            "form_pattern_aggregates": aggs,
            "history": _compact_history(history),
            "artifact_refs": artifact_refs,
            # keep minimal artifacts for traceability
            "analysis_artifacts": _safe_dict(analysis.get("artifacts_v1")),
        },
    }

    return json.dumps(prompt_obj, ensure_ascii=False)


def _sleep_backoff(attempt: int, retry_after_s: float | None) -> None:
    if retry_after_s is not None and retry_after_s > 0:
        time.sleep(retry_after_s)
        return
    # exponential backoff with jitter
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


def _call_openai(prompt: str) -> Tuple[str, dict]:
    """
    Calls OpenAI Responses API using urllib (no SDK dep).
    Returns: (text, debug_raw)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("missing_openai_api_key")

    body = {
        "model": DEFAULT_MODEL,
        "input": prompt,
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

    # Responses API: safest extraction is to walk output blocks
    text = None
    try:
        # Common shape: data["output"][0]["content"][0]["text"]
        out0 = (data.get("output") or [None])[0] or {}
        content0 = (out0.get("content") or [None])[0] or {}
        text = content0.get("text")
    except Exception:
        text = None

    if not isinstance(text, str) or not text.strip():
        # best-effort fallback: search for any "text" fields
        def _find_text(obj: Any) -> Optional[str]:
            if isinstance(obj, dict):
                if isinstance(obj.get("text"), str) and obj.get("text").strip():
                    return obj["text"]
                for v in obj.values():
                    t = _find_text(v)
                    if t:
                        return t
            if isinstance(obj, list):
                for it in obj:
                    t = _find_text(it)
                    if t:
                        return t
            return None

        text = _find_text(data)

    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("openai_parse_error: no_text_in_response")

    return text, {"response_id": data.get("id"), "model": data.get("model")}


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

    prompt = _build_prompt(payload)

    last_err: str | None = None
    last_status: int | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.time()
            text, raw_dbg = _call_openai(prompt)
            dt = time.time() - t0

            return {
                "mode": "gpt",
                "response_text": text.strip(),
                "debug": {
                    "provider": "openai",
                    "model": DEFAULT_MODEL,
                    "latency_s": round(dt, 3),
                    **raw_dbg,
                },
            }

        except urllib.error.HTTPError as e:
            last_status = int(getattr(e, "code", 0) or 0)
            last_err = f"HTTP Error {last_status}: {getattr(e, 'reason', '')}".strip()

            # Retry on rate limits + transient server errors
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

    # Fallback
    return _stub_response(payload, reason=last_err, status_code=last_status)