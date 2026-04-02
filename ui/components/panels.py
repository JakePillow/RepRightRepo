from __future__ import annotations

from collections.abc import Callable

import streamlit as st

from ui.components.primitives import render_callout, render_empty_state, render_quality_badge
from ui.config.tokens import (
    EMPTY_STATES, EXERCISES, EXERCISE_ICONS, FAULT_SEVERITY_COLORS, TEXT,
)
from ui.view_models import (
    artifact_analysis_json_path, quality_view_model, summary_metrics, top_fault_rows,
)

AnalyzeCallback = Callable[[str, float | None, object, str], None]
FollowupCallback = Callable[[str, float], None]


def render_analysis_controls(on_analyze: AnalyzeCallback) -> None:
    analysis = st.session_state.last_analysis
    exercise_locked = bool(analysis and analysis.get("exercise"))

    if exercise_locked:
        st.session_state.exercise_choice = analysis.get("exercise")
        locked_val = analysis.get("exercise", EXERCISES[0])
        icon = EXERCISE_ICONS.get(locked_val, "")
        st.selectbox(
            TEXT["inputs"]["exercise"],
            [f"{icon} {locked_val.capitalize()}"],
            disabled=True,
        )
        exercise = locked_val
    else:
        labels = [f"{EXERCISE_ICONS.get(e, '')} {e.capitalize()}" for e in EXERCISES]
        label_map = dict(zip(labels, EXERCISES))
        chosen = st.selectbox(TEXT["inputs"]["exercise"], labels, key="exercise_choice_label")
        exercise = label_map[chosen]
        st.session_state.exercise_choice = exercise

    load_kg = st.number_input(
        TEXT["inputs"]["load"], min_value=0.0, step=2.5, key="ui_load_kg"
    )
    upload = st.file_uploader(TEXT["inputs"]["upload"], type=["mp4", "mov", "avi", "mkv"])
    note   = st.text_input(TEXT["inputs"]["coach_note"])

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    if st.button(TEXT["inputs"]["analyze"], use_container_width=True, type="primary"):
        if upload is None:
            render_callout("warning", TEXT["inputs"]["upload_warning"])
        else:
            with st.spinner(TEXT["progress"]["tracking"]):
                on_analyze(exercise, load_kg if load_kg > 0 else None, upload, note)


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        st.video(str(overlay_path))
    else:
        render_empty_state(EMPTY_STATES["video"])


def render_quality_header() -> None:
    vm = quality_view_model(
        st.session_state.last_analysis,
        st.session_state.last_response,
    )
    render_quality_badge(
        TEXT["results"]["quality_title"],
        vm.score, vm.color, vm.zone_label,
        bg=vm.bg, ring=vm.ring,
    )


def render_summary_metrics() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    metrics = summary_metrics(summary)
    c1, c2, c3 = st.columns(3)
    for col, m in zip([c1, c2, c3], metrics):
        col.metric(m.label, m.value)


def render_faults_panel() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    rows = top_fault_rows(summary)
    with st.expander(TEXT["results"]["why_score"], expanded=True):
        if not rows:
            st.caption(TEXT["results"]["no_faults"])
            return
        for row in rows:
            # row is a plain string: "- CODE × N (max severity: X)"
            st.markdown(
                f"""
                <div style="
                    padding:10px 14px; margin-bottom:6px;
                    border-radius:10px;
                    background:rgba(255,255,255,0.03);
                    border:1px solid rgba(255,255,255,0.07);
                    font-size:14px; color:#e5e7eb;
                ">{row}</div>
                """,
                unsafe_allow_html=True,
            )


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

    for msg in st.session_state.history:
        role = "user" if msg.get("role") == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg.get("content", ""))
            ts = msg.get("timestamp")
            if ts:
                st.markdown(
                    f"<span style='font-size:10px;color:#4b5563;'>{ts[:16].replace('T',' ')}</span>",
                    unsafe_allow_html=True,
                )

    follow_up = st.chat_input(TEXT["chat"]["follow_up"])
    if follow_up and st.session_state.last_analysis:
        load_kg = st.session_state.get("ui_load_kg", 0.0)
        on_followup(follow_up, load_kg)
