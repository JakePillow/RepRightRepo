from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from ui.components.primitives import render_callout, render_empty_state, render_quality_badge
from ui.config.tokens import EMPTY_STATES, EXERCISES, TEXT
from ui.view_models import artifact_analysis_json_path, quality_view_model, summary_metrics, top_fault_rows


AnalyzeCallback = Callable[[str, float | None, object, str], None]
FollowupCallback = Callable[[str, float], None]


def render_analysis_controls(on_analyze: AnalyzeCallback) -> None:
    analysis = st.session_state.last_analysis
    exercise_locked = bool(analysis and analysis.get("exercise"))

    if exercise_locked:
        st.session_state.exercise_choice = analysis.get("exercise")

    exercise = st.selectbox(TEXT["inputs"]["exercise"], EXERCISES, key="exercise_choice", disabled=exercise_locked)
    load_kg = st.number_input(TEXT["inputs"]["load"], min_value=0.0, key="ui_load_kg")
    upload = st.file_uploader(TEXT["inputs"]["upload"], type=["mp4", "mov", "avi", "mkv"])
    note = st.text_input(TEXT["inputs"]["coach_note"])

    if st.button(TEXT["inputs"]["analyze"], use_container_width=True):
        if upload is None:
            render_callout("warning", TEXT["inputs"]["upload_warning"])
        else:
            on_analyze(exercise, load_kg if load_kg > 0 else None, upload, note)


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        st.video(str(overlay_path))
    else:
        render_empty_state(EMPTY_STATES["video"])


def render_quality_header() -> None:
    vm = quality_view_model(st.session_state.last_analysis, st.session_state.last_response)
    render_quality_badge(TEXT["results"]["quality_title"], vm.score, vm.color, vm.zone_label)


def render_coaching_overview() -> None:
    response = st.session_state.last_response if isinstance(st.session_state.last_response, dict) else {}
    text = response.get("response_text")
    if isinstance(text, str) and text.strip():
        st.markdown(f"#### {TEXT['results']['coaching_overview']}")
        st.write(text.strip())
    else:
        render_empty_state(EMPTY_STATES["coaching"])


def render_summary_metrics() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    metrics = summary_metrics(summary)

    c1, c2, c3 = st.columns(3)
    cols = [c1, c2, c3]
    for idx, m in enumerate(metrics):
        cols[idx].metric(m.label, m.value)


def render_faults_panel() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    rows = top_fault_rows(summary)
    with st.expander(TEXT["results"]["why_score"], expanded=False):
        if rows:
            for row in rows:
                st.write(row)
        else:
            st.caption(TEXT["results"]["no_faults"])


def render_artifacts_panel() -> None:
    p = artifact_analysis_json_path(st.session_state.last_analysis)
    if p:
        st.download_button(
            TEXT["results"]["download_json"],
            data=p.read_text(encoding="utf-8"),
            file_name=p.name,
            mime="application/json",
            use_container_width=True,
        )


def render_chat_panel(on_followup: FollowupCallback) -> None:
    if not st.session_state.history:
        render_empty_state(EMPTY_STATES["chat"])

    skip_ts = st.session_state.get("analysis_response_ts")
    for msg in st.session_state.history:
        if skip_ts and msg.get("ts") == skip_ts:
            continue
        role = "user" if msg.get("role") == "user" else "assistant"
        st.chat_message(role).write(msg.get("content"))

    follow_up = st.chat_input(TEXT["chat"]["follow_up"])
    if follow_up and st.session_state.last_analysis:
        load_kg = st.session_state.get("ui_load_kg", 0.0)
        on_followup(follow_up, load_kg)
