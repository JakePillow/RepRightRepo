from __future__ import annotations
from collections.abc import Callable
import logging
import os
import tempfile
from pathlib import Path

import streamlit as st
from ui.components.primitives import (
    render_callout, render_empty_state, render_empty_state_results,
    render_quality_badge,
)
from ui.config.tokens import EMPTY_STATES, EXERCISES, EXERCISE_ICONS, TEXT
from ui.view_models import (
    artifact_analysis_json_path, quality_view_model, summary_metrics, top_fault_rows,
)

AnalyzeCallback  = Callable[[str, float | None, object, str], None]
FollowupCallback = Callable[[str, float], None]


def render_analysis_controls(on_analyze: AnalyzeCallback) -> None:
    analysis = st.session_state.last_analysis
    exercise_locked = bool(analysis and analysis.get("exercise") and not analysis.get("_stub"))

    if exercise_locked:
        locked_val = analysis.get("exercise", EXERCISES[0])
        icon = EXERCISE_ICONS.get(locked_val, "")
        st.selectbox(TEXT["inputs"]["exercise"],
                     [f"{icon} {locked_val.capitalize()}"], disabled=True)
        exercise = locked_val
    else:
        labels    = [f"{EXERCISE_ICONS.get(e,'')} {e.capitalize()}" for e in EXERCISES]
        label_map = dict(zip(labels, EXERCISES))
        chosen    = st.selectbox(TEXT["inputs"]["exercise"], labels,
                                 key="exercise_choice_label")
        exercise  = label_map[chosen]
        st.session_state.exercise_choice = exercise

    load_kg = st.number_input(TEXT["inputs"]["load"], min_value=0.0,
                               step=2.5, key="ui_load_kg")
    upload  = st.file_uploader(TEXT["inputs"]["upload"],
                                type=["mp4", "mov", "avi", "mkv", "webm"])
    note    = st.text_input(TEXT["inputs"]["coach_note"])

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    if st.button(TEXT["inputs"]["analyze"], use_container_width=True, type="primary"):
        if upload is None:
            render_callout("warning", TEXT["inputs"]["upload_warning"])
        else:
            with st.spinner(TEXT["progress"]["tracking"]):
                on_analyze(exercise, load_kg if load_kg > 0 else None, upload, note)


def render_recent_sessions_in_main() -> None:
    from ui.chat_store import list_threads
    threads = list_threads()
    if not threads:
        return
    st.markdown(
        f"<div style='font-size:16px;font-weight:700;color:#1e293b;"
        f"margin:20px 0 10px;'>{TEXT['recent_sessions_title']}</div>",
        unsafe_allow_html=True,
    )
    for thread in threads[:5]:
        title = thread.get("title") or thread.get("thread_id", "")
        st.markdown(
            f"""<div style="background:#ffffff;border:1px solid #e2e8f0;
                border-radius:12px;padding:14px 18px;margin-bottom:8px;
                display:flex;justify-content:space-between;align-items:center;
                font-size:14px;color:#334155;font-weight:500;
                box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <span>{title}</span>
                <span style="color:#94a3b8;">›</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _reencode_to_h264(src: "Path") -> bytes | None:
    """
    Re-encode video to H.264/MP4 using OpenCV so any browser can play it.
    Returns raw MP4 bytes, or None if re-encoding fails.
    """
    cap = None
    out = None
    tmp_name = None
    try:
        import cv2

        cap = cv2.VideoCapture(str(src))
        if not cap.isOpened():
            return None
        fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        tmp    = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        tmp_name = tmp.name
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out    = cv2.VideoWriter(tmp_name, fourcc, fps, (width, height))
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)
        finally:
            cap.release()
            out.release()
            cap = None
            out = None
        data = Path(tmp_name).read_bytes()
        return data if len(data) > 1000 else None
    except Exception as e:
        logging.warning(f"[REENCODE FAILED] {e}")
        return None
    finally:
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        p = Path(str(overlay_path))
        if p.exists() and p.stat().st_size > 0:
            video_bytes = _reencode_to_h264(p)
            if video_bytes:
                st.video(video_bytes, format="video/mp4")
            else:
                st.video(p.read_bytes(), format="video/mp4")
        else:
            st.warning(f"Overlay file not found or empty at: {p}")
            render_empty_state_results()
    else:
        render_empty_state_results()


def render_quality_header() -> None:
    vm = quality_view_model(st.session_state.last_analysis, st.session_state.last_response)
    render_quality_badge(TEXT["results"]["quality_title"],
                         vm.score, vm.color, vm.zone_label,
                         bg=vm.bg, ring=vm.ring)


def render_summary_metrics() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    metrics = summary_metrics(summary)
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        with col:
            st.markdown(
                f"""<div style="text-align:center;background:#ffffff;
                    border:1px solid #e2e8f0;border-radius:16px;padding:20px 12px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <div style="font-size:11px;text-transform:uppercase;
                                letter-spacing:0.08em;color:#94a3b8;
                                font-weight:700;margin-bottom:8px;">{m.label}</div>
                    <div style="font-size:28px;font-weight:900;
                                color:#1e293b;">{m.value}</div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_faults_panel() -> None:
    summary = (st.session_state.last_analysis or {}).get("set_summary_v1") or {}
    rows    = top_fault_rows(summary)
    with st.expander(TEXT["results"]["why_score"], expanded=True):
        if not rows:
            st.caption(TEXT["results"]["no_faults"])
            return
        for row in rows:
            st.markdown(
                f"""<div style="padding:11px 16px;margin-bottom:6px;
                    border-radius:12px;background:#f8fafc;
                    border:1px solid #e2e8f0;font-size:14px;
                    color:#334155;">{row}</div>""",
                unsafe_allow_html=True,
            )


def render_artifacts_panel() -> None:
    p = artifact_analysis_json_path(st.session_state.last_analysis)
    if p:
        st.download_button(
            TEXT["results"]["download_json"],
            data=p.read_text(encoding="utf-8"),
            file_name=p.name, mime="application/json",
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
                st.caption(ts[:16].replace("T", " "))
    follow_up = st.chat_input(TEXT["chat"]["follow_up"])
    if follow_up and st.session_state.last_analysis:
        on_followup(follow_up, st.session_state.get("ui_load_kg", 0.0))


def render_coaching_overview_panel() -> None:
    t = TEXT["coaching_panel"]

    # ── Blue gradient header card ──
    coaching_text = (st.session_state.last_response or {}).get("response_text", "")
    body_html = (
        f"<p style='margin:0;font-size:14px;color:rgba(255,255,255,0.85);"
        f"line-height:1.7;white-space:pre-line;'>{coaching_text}</p>"
        if coaching_text else
        f"<p style='margin:0;font-size:14px;color:rgba(255,255,255,0.8);"
        f"line-height:1.7;'>{t['subtitle']}</p>"
    )
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#2563eb,#1e40af);
            border-radius:18px;padding:22px 22px 20px;margin-bottom:14px;color:#fff;
            box-shadow:0 4px 20px rgba(37,99,235,0.3);">
            <div style="font-size:18px;font-weight:800;margin-bottom:10px;
                        color:#ffffff;">{t['title']}</div>
            {body_html}
        </div>""",
        unsafe_allow_html=True,
    )

    # ── How it Works card — native components, no raw HTML in body ──
    with st.container():
        st.markdown(
            """<div style="background:#ffffff;border:1px solid #e2e8f0;
                border-radius:16px;padding:18px 20px 8px;margin-bottom:14px;
                box-shadow:0 1px 4px rgba(0,0,0,0.06);">
            </div>""",
            unsafe_allow_html=True,
        )
        how_col, view_col = st.columns([5, 1])
        with how_col:
            st.markdown(
                f"<div style='font-size:15px;font-weight:700;color:#1e293b;"
                f"margin-bottom:12px;'>{t['how_title']}</div>",
                unsafe_allow_html=True,
            )
        with view_col:
            st.markdown(
                f"<div style='font-size:13px;color:#2563eb;font-weight:600;"
                f"padding-top:2px;'>{t['view_all']}</div>",
                unsafe_allow_html=True,
            )
        for icon, title, desc in t["steps"]:
            ic, tx = st.columns([1, 6])
            with ic:
                st.markdown(
                    f"<div style='width:36px;height:36px;border-radius:10px;"
                    f"background:#f1f5f9;display:flex;align-items:center;"
                    f"justify-content:center;font-size:16px;margin-top:2px;'>"
                    f"{icon}</div>",
                    unsafe_allow_html=True,
                )
            with tx:
                st.markdown(
                    f"<div style='font-size:14px;font-weight:700;color:#1e293b;"
                    f"margin-bottom:2px;'>{title}</div>"
                    f"<div style='font-size:13px;color:#64748b;'>{desc}</div>",
                    unsafe_allow_html=True,
                )

    # ── Tip card ──
    st.markdown(
        f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;
            border-radius:14px;padding:14px 18px;font-size:14px;
            color:#475569;line-height:1.6;">{t['tip']}</div>""",
        unsafe_allow_html=True,
    )




