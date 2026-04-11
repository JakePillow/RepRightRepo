from __future__ import annotations
from collections.abc import Callable
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st
from ui.components.primitives import (
    render_callout, render_empty_state, render_empty_state_results,
    render_quality_badge,
)
from ui.config.tokens import EMPTY_STATES, EXERCISES, EXERCISE_ICONS, TEXT, THEME
from ui.view_models import (
    artifact_analysis_json_path, quality_view_model, summary_metrics, top_fault_rows,
)

AnalyzeCallback  = Callable[[str, float | None, object, str], None]
FollowupCallback = Callable[[str, float], None]


def render_analysis_controls(on_analyze: AnalyzeCallback) -> None:
    analysis = st.session_state.last_analysis
    busy = bool(st.session_state.get("ui_busy"))
    exercise_locked = bool(analysis and analysis.get("exercise") and not analysis.get("_stub"))

    if exercise_locked:
        locked_val = analysis.get("exercise", EXERCISES[0])
        icon = EXERCISE_ICONS.get(locked_val, "")
        st.selectbox(TEXT["inputs"]["exercise"],
                     [f"{icon} {locked_val.capitalize()}"], disabled=True)
        exercise = locked_val
        st.caption(TEXT["inputs"]["exercise_locked"])
    else:
        labels    = [f"{EXERCISE_ICONS.get(e,'')} {e.capitalize()}" for e in EXERCISES]
        label_map = dict(zip(labels, EXERCISES))
        current_exercise = st.session_state.get("exercise_choice", EXERCISES[0])
        default_label = next(
            (label for label, value in label_map.items() if value == current_exercise),
            labels[0],
        )
        if "exercise_choice_label" not in st.session_state:
            st.session_state.exercise_choice_label = default_label
        chosen = st.selectbox(
            TEXT["inputs"]["exercise"],
            labels,
            key="exercise_choice_label",
            disabled=busy,
            help=TEXT["inputs"]["busy_help"] if busy else None,
        )
        exercise  = label_map[chosen]
        st.session_state.exercise_choice = exercise

    load_kg = st.number_input(
        TEXT["inputs"]["load"],
        min_value=0.0,
        step=2.5,
        key="ui_load_kg",
        disabled=busy,
    )
    upload = st.file_uploader(
        TEXT["inputs"]["upload"],
        type=["mp4", "mov", "avi", "mkv", "webm"],
        key="uploaded_video",
        disabled=busy,
    )
    note = st.text_input(TEXT["inputs"]["coach_note"], key="coach_note_input", disabled=busy)

    st.markdown("<div style='margin-top:6px'></div>", unsafe_allow_html=True)
    if st.button(TEXT["inputs"]["analyze"], use_container_width=True, type="primary", disabled=busy):
        if upload is None:
            render_callout("warning", TEXT["inputs"]["upload_warning"])
        else:
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
            f"""<div style="background:{THEME['card_bg']};border:1px solid {THEME['border']};
                border-radius:12px;padding:14px 18px;margin-bottom:8px;
                display:flex;justify-content:space-between;align-items:center;
                font-size:14px;color:{THEME['text_soft']};font-weight:600;
                box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                <span>{title}</span>
                <span style="color:{THEME['text_muted']};">›</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _video_stream_info(src: "Path") -> dict[str, str] | None:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None
    try:
        proc = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,codec_tag_string,pix_fmt",
                "-of",
                "json",
                str(src),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout or "{}")
        streams = payload.get("streams") if isinstance(payload, dict) else []
        if not streams:
            return None
        stream = streams[0]
        if not isinstance(stream, dict):
            return None
        return {k: str(v) for k, v in stream.items() if v}
    except Exception as e:
        logging.warning(f"[REENCODE FAILED] {e}")
        return None


def _needs_browser_transcode(src: "Path") -> bool:
    if src.suffix.lower() != ".mp4":
        return False
    info = _video_stream_info(src)
    if info is None:
        return False
    codec = info.get("codec_name", "").lower()
    tag = info.get("codec_tag_string", "").lower()
    pix_fmt = info.get("pix_fmt", "").lower()
    if codec != "h264":
        return True
    if tag and tag not in {"avc1", "h264"}:
        return True
    if pix_fmt and pix_fmt not in {"yuv420p", "yuvj420p"}:
        return True
    return False


def _reencode_to_h264(src: "Path") -> bytes | None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return None

    tmp_name = None
    try:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        tmp_name = tmp.name
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(src),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                tmp_name,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            err = (proc.stderr or "").strip()
            logging.warning(f"[REENCODE FAILED] {err[:300]}")
            return None
        data = Path(tmp_name).read_bytes()
        return data if len(data) > 1000 else None
    except Exception as e:
        logging.warning(f"[REENCODE FAILED] {e}")
        return None
    finally:
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        p = Path(str(overlay_path))
        if p.exists() and p.stat().st_size > 0:
            if p.suffix.lower() == ".webm":
                st.video(p.read_bytes(), format="video/webm")
                return

            if p.suffix.lower() == ".mp4" and not _needs_browser_transcode(p):
                st.video(str(p))
                return

            video_bytes = _reencode_to_h264(p)
            if video_bytes:
                st.video(video_bytes, format="video/mp4")
            else:
                st.video(str(p))
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
                f"""<div style="text-align:center;background:{THEME['card_bg']};
                    border:1px solid {THEME['border']};border-radius:16px;padding:20px 12px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <div style="font-size:11px;text-transform:uppercase;
                                letter-spacing:0.08em;color:{THEME['text_muted']};
                                font-weight:700;margin-bottom:8px;">{m.label}</div>
                    <div style="font-size:28px;font-weight:900;
                                color:{THEME['text']};">{m.value}</div>
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
                    border-radius:12px;background:{THEME['card_bg_alt']};
                    border:1px solid {THEME['border']};font-size:14px;
                    color:{THEME['text_soft']};">{row}</div>""",
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
    busy = bool(st.session_state.get("ui_busy"))
    if not st.session_state.history:
        render_empty_state(EMPTY_STATES["chat"])
    for msg in st.session_state.history:
        role = "user" if msg.get("role") == "user" else "assistant"
        with st.chat_message(role):
            st.write(msg.get("content", ""))
            ts = msg.get("timestamp")
            if ts:
                st.caption(ts[:16].replace("T", " "))
    follow_up = st.chat_input(
        TEXT["chat"]["follow_up"] if st.session_state.last_analysis else TEXT["chat"]["follow_up_disabled"],
        disabled=busy or not bool(st.session_state.last_analysis),
    )
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
        f"""<div style="background:linear-gradient(135deg,{THEME['accent']},{THEME['accent_hover']});
            border-radius:18px;padding:22px 22px 20px;margin-bottom:14px;color:#fff;
            box-shadow:0 4px 20px rgba(37,99,235,0.3);">
            <div style="font-size:18px;font-weight:800;margin-bottom:10px;
                        color:#ffffff;">{t['title']}</div>
            {body_html}
        </div>""",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            f"<div style='font-size:15px;font-weight:700;color:{THEME['text']};margin-bottom:12px;'>{t['how_title']}</div>",
            unsafe_allow_html=True,
        )
        for icon, title, desc in t["steps"]:
            ic, tx = st.columns([1, 6])
            with ic:
                st.markdown(
                    f"<div style='width:36px;height:36px;border-radius:10px;"
                    f"background:{THEME['card_bg_alt']};display:flex;align-items:center;"
                    f"justify-content:center;font-size:16px;margin-top:2px;'>"
                    f"{icon}</div>",
                    unsafe_allow_html=True,
                )
            with tx:
                st.markdown(
                    f"<div style='font-size:14px;font-weight:700;color:{THEME['text']};"
                    f"margin-bottom:2px;'>{title}</div>"
                    f"<div style='font-size:13px;color:{THEME['text_muted']};'>{desc}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown(
        f"""<div style="background:{THEME['card_bg_alt']};border:1px solid {THEME['border']};
            border-radius:14px;padding:14px 18px;font-size:14px;
            color:{THEME['text_soft']};line-height:1.6;">{t['tip']}</div>""",
        unsafe_allow_html=True,
    )




