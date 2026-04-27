from __future__ import annotations

import importlib
import inspect
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import streamlit as st

from repright import coach_payload as coach_payload_module
from repright.analyser import RepRightAnalyzer
from repright.llm_wrapper import run_coach
from ui.config.tokens import TEXT
from ui.runtime import demo_force_stub


def safe_tmp_video(upload) -> Path:
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)

    p = Path(path)
    p.write_bytes(upload.getbuffer())
    return p


def _build_coach_payload_compat(
    analysis: dict[str, Any],
    *,
    message: str = "",
    load_kg: float | None = None,
    history: list[dict[str, Any]] | None = None,
    previous_analysis: dict[str, Any] | None = None,
    previous_load_kg: float | None = None,
):
    try:
        module = importlib.reload(coach_payload_module)
    except Exception:
        logging.exception("Failed to reload repright.coach_payload; using existing module")
        module = coach_payload_module

    fn = module.build_coach_payload
    kwargs: dict[str, Any] = {
        "message": message,
        "load_kg": load_kg,
        "history": history,
    }
    try:
        params = inspect.signature(fn).parameters
        if "previous_analysis" in params:
            kwargs["previous_analysis"] = previous_analysis
        if "previous_load_kg" in params:
            kwargs["previous_load_kg"] = previous_load_kg
    except Exception:
        logging.exception("Could not inspect build_coach_payload signature; using base arguments only")

    return fn(analysis, **kwargs)


def run_analysis_pipeline(
    upload,
    exercise: str,
    user_message: str,
    load_kg: float | None,
    history: list[dict[str, Any]],
    previous_analysis: dict[str, Any] | None = None,
    previous_load_kg: float | None = None,
):
    tmp_path = safe_tmp_video(upload)

    progress_status = st.empty()
    progress_status.caption(TEXT["progress"]["tracking"])
    progress = st.progress(0)

    analyzer = RepRightAnalyzer()
    analysis = analyzer.analyze(str(tmp_path), exercise)
    _op = analysis.get("overlay_path") or (analysis.get("artifacts_v1") or {}).get("overlay_path")
    logging.warning(
        "[OVERLAY DEBUG] path='%s' | exists=%s | size=%s",
        _op,
        os.path.exists(str(_op)) if _op else "NO PATH",
        os.path.getsize(str(_op)) if _op and os.path.exists(str(_op)) else 0,
    )

    progress_status.caption(TEXT["progress"]["context"])
    progress.progress(60)

    payload = _build_coach_payload_compat(
        analysis,
        message=user_message,
        load_kg=load_kg,
        history=history[-6:],
        previous_analysis=previous_analysis,
        previous_load_kg=previous_load_kg,
    )

    progress_status.caption(TEXT["progress"]["coach"])
    progress.progress(85)

    response = run_coach(payload, mode="stub" if demo_force_stub() else "auto")

    progress_status.caption(TEXT["progress"]["done"])
    progress.progress(100)
    time.sleep(0.1)
    progress.empty()
    progress_status.empty()

    return analysis, payload, response


def run_followup_coaching(analysis: dict[str, Any], follow_up: str, load_kg: float, history: list[dict[str, Any]]):
    payload = _build_coach_payload_compat(
        analysis,
        message=follow_up,
        load_kg=load_kg,
        history=history[-8:],
    )
    response = run_coach(payload, mode="stub" if demo_force_stub() else "auto")
    return payload, response
