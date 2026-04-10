from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_store import load_thread, new_thread_id, now_iso, save_thread, thread_title
from ui.components import panels
from ui.components.primitives import render_empty_state, render_restore_status_badge, render_section
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


def inject_global_css() -> None:
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        #MainMenu, header[data-testid="stHeader"],
        footer, [data-testid="stToolbar"],
        [data-testid="stDecoration"], .stDeployButton { display:none !important; }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background: #eef0f5 !important;
            font-family: 'Inter', -apple-system, sans-serif !important;
            color: #1e293b !important;
        }
        .block-container {
            padding-top: 28px !important;
            padding-left: 32px !important;
            padding-right: 32px !important;
            max-width: 100% !important;
        }
        [data-testid="stSidebar"] {
            background: #1b2b47 !important;
            border-right: none !important;
            min-width: 210px !important;
            max-width: 210px !important;
        }
        [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
        [data-testid="stSidebar"] .stMarkdown p {
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: #64748b !important;
            margin: 16px 0 6px !important;
        }
        [data-testid="stSidebar"] .stButton > button {
            background: #243756 !important;
            color: #e2e8f0 !important;
            border: none !important;
            border-radius: 10px !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            text-align: left !important;
            padding: 9px 14px !important;
            margin-bottom: 4px !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover {
            background: #2f4a6e !important;
        }
        section[data-testid="stMain"] > div {
            background: #eef0f5 !important;
        }
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: #ffffff !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 10px !important;
            color: #1e293b !important;
            font-size: 15px !important;
        }
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
        }
        .stSelectbox > div > div {
            background: #ffffff !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 10px !important;
            color: #1e293b !important;
        }
        .stTextInput > label, .stNumberInput > label,
        .stSelectbox > label, .stFileUploader > label {
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: #64748b !important;
        }
        div[data-testid="stFileUploader"] section {
            background: #ffffff !important;
            border: 1.5px dashed #cbd5e1 !important;
            border-radius: 14px !important;
        }
        button[kind="primary"] {
            background: #2f5fe8 !important;
            color: #fff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 15px !important;
            box-shadow: 0 4px 18px rgba(47,95,232,0.3) !important;
        }
        button[kind="primary"]:hover { opacity: 0.9 !important; }
        div[data-testid="stExpander"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
        }
        div[data-testid="stExpander"] summary {
            font-size: 12px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: #64748b !important;
        }
        div[data-testid="stChatMessage"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
        }
        div[data-testid="stChatInput"] > div {
            background: #ffffff !important;
            border: 1.5px solid #e2e8f0 !important;
            border-radius: 14px !important;
        }
        .stDownloadButton > button {
            background: #ffffff !important;
            color: #2563eb !important;
            border: 1.5px solid #bfdbfe !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 13px !important;
        }
        .stSpinner > div { border-top-color: #2563eb !important; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
        </style>""", unsafe_allow_html=True)


def render_sidebar() -> None:
    from ui.chat_store import list_threads
    with st.sidebar:
        st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;padding:20px 0 18px;">
                <div style="width:34px;height:34px;border-radius:50%;
                            background:linear-gradient(135deg,#f97316,#ea580c);
                            display:flex;align-items:center;justify-content:center;
                            font-size:16px;">🏋</div>
                <span style="font-size:17px;font-weight:900;
                             color:#ffffff;letter-spacing:-0.02em;">RepRight</span>
            </div>""", unsafe_allow_html=True)

        if st.button(TEXT["sidebar"]["new_chat"], use_container_width=True):
            start_new_chat(st.session_state.get("exercise_choice") or "bench")
            st.rerun()
        if st.button(TEXT["sidebar"]["clear_chat"], use_container_width=True):
            reset_group("chat")
            st.session_state.last_payload  = None
            st.session_state.last_response = None
            save_thread(st.session_state.thread_id)
            st.rerun()

        all_threads = list_threads()
        if all_threads:
            st.markdown(TEXT["sidebar"]["sessions_header"])
            for thread in all_threads[:6]:
                tid = thread.get("thread_id")
                if st.button(thread.get("title") or tid,
                             key=f"top_{tid}", use_container_width=True):
                    load_thread(tid)
                    st.rerun()
        if len(all_threads) > 6:
            st.markdown(TEXT["sidebar"]["recent_header"])
            for thread in all_threads[6:12]:
                tid = thread.get("thread_id")
                if st.button(thread.get("title") or tid,
                             key=f"rec_{tid}", use_container_width=True):
                    load_thread(tid)
                    st.rerun()


def start_new_chat(exercise: str) -> None:
    thread_id = new_thread_id(exercise)
    st.session_state.thread_id         = thread_id
    st.session_state.thread_created_at = now_iso()
    st.session_state.thread_title      = thread_title(
        st.session_state.thread_created_at, exercise)
    st.session_state.exercise_choice   = exercise
    reset_group("chat")
    reset_group("analysis")
    save_thread(thread_id)


def on_analyze(exercise, use_load, upload, note) -> None:
    analysis, payload, response = run_analysis_pipeline(
        upload=upload, exercise=exercise, user_message=note,
        load_kg=use_load, history=st.session_state.history,
    )
    st.session_state.last_analysis = analysis
    st.session_state.last_payload  = payload
    st.session_state.last_response = response
    if note:
        append_history("user", note, now_iso())
    append_history("assistant", response.get("response_text", ""), now_iso())
    save_thread(st.session_state.thread_id)


def on_followup(follow_up, load_kg) -> None:
    payload, response = run_followup_coaching(
        analysis=st.session_state.last_analysis,
        follow_up=follow_up, load_kg=load_kg,
        history=st.session_state.history,
    )
    st.session_state.last_payload  = payload
    st.session_state.last_response = response
    append_history("user", follow_up, now_iso())
    append_history("assistant", response.get("response_text", ""), now_iso())
    save_thread(st.session_state.thread_id)
    st.rerun()


def main() -> None:
    st.set_page_config(page_title="RepRight", page_icon="🏋️", layout="wide")
    inject_global_css()
    initialize_session_state()

    if st.session_state.thread_id is None:
        start_new_chat(st.session_state.get("exercise_choice") or "bench")

    render_sidebar()

    overlay_path = resolve_overlay_path(
        st.session_state.last_payload, st.session_state.last_analysis,
    )

    # Page header
    hcol, _ = st.columns([10, 1])
    with hcol:
        st.markdown(
            f"<h1 style='font-size:26px;font-weight:900;color:#1e293b;"
            f"letter-spacing:-0.02em;margin:0 0 22px;'>"
            f"{TEXT['main_title']}</h1>",
            unsafe_allow_html=True,
        )

    centre, right = st.columns([1.55, 1])

    with centre:
        # Input card — white rounded card, no stray open divs
        with st.container(border=True):
            panels.render_analysis_controls(on_analyze)

        # Empty state / overlay
        panels.render_overlay_panel(overlay_path)

        # Recent sessions
        panels.render_recent_sessions_in_main()

    with right:
        render_restore_status_badge(st.session_state.get('restore_status'))
        panels.render_coaching_overview_panel()

        if st.session_state.last_analysis or st.session_state.last_response:
            panels.render_quality_header()
            panels.render_summary_metrics()
            panels.render_faults_panel()
            panels.render_artifacts_panel()

        panels.render_chat_panel(on_followup)


if __name__ == "__main__":
    main()

