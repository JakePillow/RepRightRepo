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
    "render_overlay_panel":     panels.render_overlay_panel,
    "render_quality_header":    panels.render_quality_header,
    "render_summary_metrics":   panels.render_summary_metrics,
    "render_faults_panel":      panels.render_faults_panel,
    "render_artifacts_panel":   panels.render_artifacts_panel,
    "render_chat_panel":        panels.render_chat_panel,
}


# ── Global CSS ────────────────────────────────────────────────────────────────
def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        /* Base */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background-color: #0a0c10 !important;
            color: #e5e7eb !important;
        }
        .block-container {
            padding-top: 1.25rem !important;
            max-width: 1440px !important;
        }
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #0d1117 !important;
            border-right: 1px solid rgba(255,255,255,0.07) !important;
        }
        /* Metric cards */
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 14px !important;
            padding: 14px !important;
        }
        /* File uploader */
        div[data-testid="stFileUploader"] section {
            background: rgba(255,255,255,0.02) !important;
            border: 1px dashed rgba(255,255,255,0.14) !important;
            border-radius: 12px !important;
        }
        /* Expander */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 14px !important;
            background: rgba(255,255,255,0.02) !important;
        }
        /* Chat messages */
        div[data-testid="stChatMessage"] {
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
        }
        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: #111827 !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
            color: #f3f4f6 !important;
        }
        /* Labels */
        .stTextInput > label, .stNumberInput > label,
        .stSelectbox > label, .stFileUploader > label {
            font-size: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
            color: #9ca3af !important;
        }
        /* Primary button */
        button[kind="primary"] {
            background: linear-gradient(135deg,#2563eb,#1d4ed8) !important;
            border-radius: 12px !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
        }
        /* Download button */
        .stDownloadButton > button {
            background: #0d1117 !important;
            color: #60a5fa !important;
            border: 1px solid #1e3a5f !important;
            border-radius: 10px !important;
        }
        /* Headings */
        h1, h2, h3 { color: #f9fafb !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Sidebar logo ──────────────────────────────────────────────────────────────
def render_logo() -> None:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;
                    padding:10px 0 18px 0;">
            <div style="width:30px;height:30px;border-radius:8px;
                        background:linear-gradient(135deg,#2563eb,#7c3aed);
                        display:flex;align-items:center;justify-content:center;
                        font-size:15px;">🏋</div>
            <span style="font-size:17px;font-weight:700;
                         letter-spacing:-0.02em;color:#f9fafb;">RepRight</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Chat lifecycle ────────────────────────────────────────────────────────────
def start_new_chat(exercise: str) -> None:
    thread_id = new_thread_id(exercise)
    st.session_state.thread_id          = thread_id
    st.session_state.thread_created_at  = now_iso()
    st.session_state.thread_title       = thread_title(st.session_state.thread_created_at, exercise)
    st.session_state.exercise_choice    = exercise
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
    st.session_state.last_payload  = payload
    st.session_state.last_response = response
    if note:
        append_history("user", note, now_iso())
    append_history("assistant", response.get("response_text", ""), now_iso())
    save_thread(st.session_state.thread_id)


def on_followup(follow_up: str, load_kg: float) -> None:
    payload, response = run_followup_coaching(
        analysis=st.session_state.last_analysis,
        follow_up=follow_up,
        load_kg=load_kg,
        history=st.session_state.history,
    )
    st.session_state.last_payload  = payload
    st.session_state.last_response = response
    append_history("user", follow_up, now_iso())
    append_history("assistant", response.get("response_text", ""), now_iso())
    save_thread(st.session_state.thread_id)
    st.rerun()


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    from ui.chat_store import list_threads

    with st.sidebar:
        render_logo()
        st.markdown(
            "<hr style='border-color:rgba(255,255,255,0.07);margin:0 0 10px 0'>",
            unsafe_allow_html=True,
        )
        if st.button(TEXT["sidebar"]["new_chat"], use_container_width=True):
            start_new_chat(st.session_state.get("exercise_choice") or "bench")
            st.rerun()

        if st.button(TEXT["sidebar"]["clear_chat"], use_container_width=True):
            reset_group("chat")
            st.session_state.last_payload  = None
            st.session_state.last_response = None
            save_thread(st.session_state.thread_id)
            st.rerun()

        st.markdown(TEXT["sidebar"]["chats_header"])
        for thread in list_threads():
            tid = thread.get("thread_id")
            if st.button(thread.get("title") or tid, key=tid, use_container_width=True):
                load_thread(tid)
                st.rerun()


# ── Section renderer (closure bug fixed) ─────────────────────────────────────
def render_column_sections(
    sections: list[dict], extra_context: dict | None = None
) -> None:
    context = extra_context or {}

    for section in sections:
        enabled  = SECTION_FLAGS.get(section["enabled_flag"], True)
        renderer = RENDERERS[section["renderer"]]

        def _body(sec=section, rend=renderer, ctx=context) -> None:
            sid = sec["id"]
            if sid == "left_input_panel":
                rend(on_analyze)
            elif sid == "left_overlay_panel":
                rend(ctx.get("overlay_path"))
            elif sid == "right_chat":
                rend(on_followup)
            else:
                rend()

        render_section(enabled, _body)


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(
        page_title=PAGE["title"],
        page_icon="🏋️",
        layout=PAGE["layout"],
    )
    inject_global_css()
    initialize_session_state()

    if st.session_state.thread_id is None:
        start_new_chat(st.session_state.get("exercise_choice") or "bench")

    render_sidebar()

    overlay_path = resolve_overlay_path(
        st.session_state.last_payload,
        st.session_state.last_analysis,
    )

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
