from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_store import load_thread, new_thread_id, now_iso, save_thread, thread_title
from ui.components import panels
from ui.components.primitives import render_empty_state, render_section
from ui.config.layout import LEFT_SECTIONS, RIGHT_SECTIONS
from ui.config.tokens import PAGE, SECTION_FLAGS, TEXT
from ui.services import run_analysis_pipeline, run_followup_coaching
from ui.state import append_history, initialize_session_state, reset_group
from ui.view_models import resolve_overlay_path


RENDERERS = {
    "render_analysis_controls": panels.render_analysis_controls,
    "render_overlay_panel": panels.render_overlay_panel,
    "render_quality_header": panels.render_quality_header,
    "render_coaching_overview": panels.render_coaching_overview,
    "render_summary_metrics": panels.render_summary_metrics,
    "render_faults_panel": panels.render_faults_panel,
    "render_artifacts_panel": panels.render_artifacts_panel,
    "render_chat_panel": panels.render_chat_panel,
}


def apply_accessibility_styles() -> None:
    st.markdown(
        """
        <style>
          :root { --text-strong: #0f172a; --text-muted: #334155; }
          html, body, [data-testid="stAppViewContainer"] { color: var(--text-strong) !important; }
          p, li, label, span, div, small, .stCaption, .stMarkdown { color: var(--text-strong) !important; }
          [data-testid="stSidebar"] * { color: var(--text-strong) !important; }
          [data-testid="stChatMessageContent"] * { color: var(--text-strong) !important; }
          .stButton > button, .stDownloadButton > button {
            color: #0b3dd9 !important;
            border-color: #94a3b8 !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def start_new_chat(exercise: str) -> None:
    thread_id = new_thread_id(exercise)
    st.session_state.thread_id = thread_id
    st.session_state.thread_created_at = now_iso()
    st.session_state.thread_title = thread_title(st.session_state.thread_created_at, exercise)
    st.session_state.exercise_choice = exercise

    reset_group("chat")
    reset_group("analysis")

    save_thread(thread_id)


def on_analyze(exercise: str, use_load: float | None, upload, note: str) -> None:
    analysis, payload, response = run_analysis_pipeline(
        upload=upload,
        exercise=exercise,
        user_message=note,
        load_kg=use_load,
        history=st.session_state.history,
    )

    st.session_state.last_analysis = analysis
    st.session_state.last_payload = payload
    st.session_state.last_response = response

    if note:
        append_history("user", note, now_iso())
    assistant_ts = now_iso()
    append_history("assistant", response.get("response_text", ""), assistant_ts)
    st.session_state.analysis_response_ts = assistant_ts
    save_thread(st.session_state.thread_id)


def on_followup(follow_up: str, load_kg: float) -> None:
    payload, response = run_followup_coaching(
        analysis=st.session_state.last_analysis,
        follow_up=follow_up,
        load_kg=load_kg,
        history=st.session_state.history,
    )

    st.session_state.last_payload = payload
    st.session_state.last_response = response

    append_history("user", follow_up, now_iso())
    append_history("assistant", response.get("response_text", ""), now_iso())
    save_thread(st.session_state.thread_id)
    st.rerun()


def render_sidebar() -> None:
    from ui.chat_store import list_threads

    with st.sidebar:
        if st.button(TEXT["sidebar"]["new_chat"], use_container_width=True):
            start_new_chat(st.session_state.get("exercise_choice") or "bench")
            st.rerun()

        if st.button(TEXT["sidebar"]["clear_chat"], use_container_width=True):
            reset_group("chat")
            st.session_state.last_payload = None
            st.session_state.last_response = None
            save_thread(st.session_state.thread_id)
            st.rerun()

        st.markdown(TEXT["sidebar"]["chats_header"])

        for thread in list_threads():
            tid = thread.get("thread_id")
            if st.button(thread.get("title") or tid, key=tid, use_container_width=True):
                load_thread(tid)
                st.rerun()


def render_column_sections(sections: list[dict], extra_context: dict | None = None) -> None:
    context = extra_context or {}

    for section in sections:
        enabled = SECTION_FLAGS.get(section["enabled_flag"], True)
        renderer = RENDERERS[section["renderer"]]

        def _body() -> None:
            if section["id"] == "left_input_panel":
                renderer(on_analyze)
            elif section["id"] == "left_overlay_panel":
                renderer(context.get("overlay_path"))
            elif section["id"] == "right_chat":
                renderer(on_followup)
            else:
                renderer()

        render_section(enabled, _body)


def main() -> None:
    st.set_page_config(page_title=PAGE["title"], layout=PAGE["layout"])
    initialize_session_state()
    apply_accessibility_styles()

    if st.session_state.thread_id is None:
        start_new_chat(st.session_state.get("exercise_choice") or "bench")

    render_sidebar()

    overlay_path = resolve_overlay_path(st.session_state.last_payload, st.session_state.last_analysis)

    left, right = st.columns(PAGE["columns"])
    with left:
        render_column_sections(LEFT_SECTIONS, extra_context={"overlay_path": overlay_path})

    with right:
        has_results = st.session_state.last_analysis or st.session_state.last_response
        if has_results:
            render_column_sections(RIGHT_SECTIONS)
        else:
            render_empty_state(TEXT["states"]["empty_results"])


if __name__ == "__main__":
    main()
