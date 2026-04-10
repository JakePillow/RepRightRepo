from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import streamlit as st

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach
from ui.config.tokens import TEXT


def safe_tmp_video(upload) -> Path:
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)

    p = Path(path)
    p.write_bytes(upload.getbuffer())
    return p


def run_analysis_pipeline(upload, exercise: str, user_message: str, load_kg: float | None, history: list[dict[str, Any]]):
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

    payload = build_coach_payload(
        analysis,
        message=user_message,
        load_kg=load_kg,
        history=history[-6:],
    )

    progress_status.caption(TEXT["progress"]["coach"])
    progress.progress(85)

    response = run_coach(payload)

    progress_status.caption(TEXT["progress"]["done"])
    progress.progress(100)
    time.sleep(0.1)
    progress.empty()
    progress_status.empty()

    return analysis, payload, response


def run_followup_coaching(analysis: dict[str, Any], follow_up: str, load_kg: float, history: list[dict[str, Any]]):
    payload = build_coach_payload(
        analysis,
        message=follow_up,
        load_kg=load_kg,
        history=history[-8:],
    )
    response = run_coach(payload)
    return payload, response
