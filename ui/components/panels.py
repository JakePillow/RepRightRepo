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

    if st.session_state.get("clear_coach_note_pending"):
        st.session_state.coach_note_input = ""
        st.session_state.clear_coach_note_pending = False

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


<<<<<<< Updated upstream
def render_chat_panel(on_followup: FollowupCallback) -> None:
=======
def render_comparison_panel() -> None:
    vm = comparison_view_model(st.session_state.get("last_payload"))
    if vm is None or not vm.metrics:
        return

    st.markdown(
        f"""<div class="rr-comparison-shell">
            <div class="rr-section-kicker">{vm.headline}</div>
            <div class="rr-comparison-summary">{vm.summary}</div>
            <div class="rr-comparison-note">
                These cards show set-to-set change. The large value is the difference from the previous valid set to the current set.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    cols = st.columns(min(3, len(vm.metrics)))
    for idx, metric in enumerate(vm.metrics):
        with cols[idx % len(cols)]:
            st.markdown(
                f"""<div class="rr-comparison-metric rr-comparison-metric--{metric.tone}">
                    <div class="rr-comparison-metric__label">{metric.label}</div>
                    <div class="rr-comparison-metric__delta-label">Change vs previous set</div>
                    <div class="rr-comparison-metric__delta">{metric.delta}</div>
                    <div class="rr-comparison-metric__values">
                        <span>Previous set: {metric.previous}</span>
                        <span>Current set: {metric.current}</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    if vm.fault_rows:
        st.markdown(
            "<div class='rr-section-kicker' style='margin:14px 0 8px;'>Fault Changes</div>",
            unsafe_allow_html=True,
        )
        for row in vm.fault_rows:
            st.markdown(f"""<div class="rr-fault-row rr-fault-row--comparison">{row}</div>""", unsafe_allow_html=True)


def _analysis_score_value() -> float | None:
    response = st.session_state.get("last_response") or {}
    structured = response.get("structured") if isinstance(response, dict) else {}
    if isinstance(structured, dict):
        score = structured.get("overall_score")
        if isinstance(score, (int, float)):
            return float(score)

    summary = (st.session_state.get("last_analysis") or {}).get("set_summary_v1") or {}
    score = summary.get("quality_score") or summary.get("quality_score_pct")
    return float(score) if isinstance(score, (int, float)) else None


def _coach_summary_card() -> None:
    analysis = st.session_state.get("last_analysis") or {}
    summary = analysis.get("set_summary_v1") or {}
    compare_vm = comparison_view_model(st.session_state.get("last_payload"))
    exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "analysis").capitalize()
    reps = summary.get("n_reps", "—")
    avg_rom = summary.get("avg_rom")
    avg_rom_label = f"{float(avg_rom):.2f}" if isinstance(avg_rom, (int, float)) else "n/a"
    load_kg = st.session_state.get("ui_load_kg")
    score = _analysis_score_value()
    score_label = f"{score:.0f}" if isinstance(score, (int, float)) else "—"
    load_label = f"{float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "Load: n/a"

    st.markdown(
        f"""<div class="rr-hero-card rr-hero-card--analysis">
            <div class="rr-hero-card__head">
                <div>
                    <div class="rr-kicker rr-kicker--light">Analysis Snapshot</div>
                    <div class="rr-hero-card__title">{exercise}</div>
                    <div class="rr-hero-card__copy">
                        Open the full analysis for quality breakdown, rep metrics, recurring faults, and export tools.
                    </div>
                </div>
                <div class="rr-hero-card__score">
                    <div class="rr-kicker rr-kicker--light">Lift Quality</div>
                    <div class="rr-hero-card__score-value">{score_label}</div>
                    <div class="rr-hero-card__score-scale">/100</div>
                </div>
            </div>
            <div class="rr-chip-row">
                <span class="rr-chip rr-chip--hero">Reps: {reps}</span>
                <span class="rr-chip rr-chip--hero">Avg ROM: {avg_rom_label}</span>
                <span class="rr-chip rr-chip--hero">{load_label}</span>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )
    if compare_vm and compare_vm.metrics:
        chips = "".join(
            f"""<span class="rr-chip rr-chip--compare rr-chip--compare-{metric.tone}">
                {metric.label} change: {metric.delta}
            </span>"""
            for metric in compare_vm.metrics[:4]
        )
        st.markdown(
            f"""<div class="rr-compare-strip">
                <div class="rr-section-kicker">Latest Comparison</div>
                <div class="rr-compare-strip__summary">{compare_vm.summary}</div>
                <div class="rr-comparison-note">
                    Showing the change from the previous valid set to this one.
                </div>
                <div class="rr-chip-row">{chips}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _coach_welcome_card() -> None:
    t = TEXT["coaching_panel"]
    steps = "".join(
        f"""<div class="rr-hero-step">
            <div class="rr-hero-step__icon">{icon}</div>
            <div>
                <div class="rr-hero-step__title">{title}</div>
                <div class="rr-hero-step__desc">{desc}</div>
            </div>
        </div>"""
        for icon, title, desc in t["steps"]
    )
    st.markdown(
        f"""<div class="rr-hero-card rr-hero-card--welcome">
            <div class="rr-kicker rr-kicker--light">Coach Chat</div>
            <div class="rr-hero-card__title">{t['title']}</div>
            <div class="rr-hero-card__copy">{t['subtitle']}</div>
            {steps}
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption(t["tip"])


def _render_analysis_dialog() -> None:
    @st.dialog("Analysis Snapshot", width="large")
    def _analysis_dialog() -> None:
        analysis = st.session_state.get("last_analysis") or {}
        response = st.session_state.get("last_response") or {}
        exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "analysis").capitalize()
        load_kg = st.session_state.get("ui_load_kg")
        load_label = f"{float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "n/a"
        response_text = response.get("response_text", "") if isinstance(response, dict) else ""

        st.markdown(
            f"""<div class="rr-dialog-hero">
                <div class="rr-dialog-hero__head">
                    <div>
                        <div class="rr-section-kicker">Detailed View</div>
                        <div class="rr-dialog-hero__title">{exercise}</div>
                    </div>
                    <div class="rr-dialog-hero__load">Load: {load_label}</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        render_quality_header()
        render_summary_metrics()
        render_comparison_panel()
        render_faults_panel()
        render_artifacts_panel()

        if response_text:
            st.markdown("**Latest Coach Reply**")
            st.markdown(
                f"""<div class="rr-assistant-note">{response_text}</div>""",
                unsafe_allow_html=True,
            )

        if st.button("Back To Chat", use_container_width=True, key="collapse_analysis_dialog"):
            st.rerun()

    _analysis_dialog()


def _render_coach_composer(
    on_analyze: AnalyzeCallback,
    on_followup: FollowupCallback,
    *,
    busy: bool,
    has_analysis: bool,
    exercise_locked: bool,
) -> tuple[str, str] | None:
    caption = (
        "Upload another clip of this same exercise to compare it against the latest analysis, or just send a text follow-up."
        if has_analysis else
        "Choose an exercise, add the load if you want it considered, then upload your first set to start the chat."
    )
    title = (
        "Upload a comparison or send a follow-up"
        if has_analysis else
        "Start with your set"
    )

    st.markdown(
        f"""<div class="rr-coach-composer-intro">
            <div class="rr-section-kicker">Session Input</div>
            <div class="rr-coach-composer-intro__title">{title}</div>
            <div class="rr-coach-composer-intro__copy">{caption}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    if exercise_locked:
        locked_val = (st.session_state.get("last_analysis") or {}).get("exercise", EXERCISES[0])
        icon = EXERCISE_ICONS.get(locked_val, "")
        st.selectbox(
            TEXT["inputs"]["exercise"],
            [f"{icon} {str(locked_val).capitalize()}"],
            disabled=True,
            key="coach_locked_exercise",
        )
        exercise = str(locked_val)
    else:
        labels = [f"{EXERCISE_ICONS.get(e, '')} {e.capitalize()}" for e in EXERCISES]
        label_map = dict(zip(labels, EXERCISES))
        current_exercise = st.session_state.get("exercise_choice") or EXERCISES[0]
        current_label = next(
            (label for label, value in label_map.items() if value == current_exercise),
            labels[0],
        )
        selected = st.selectbox(
            TEXT["inputs"]["exercise"],
            labels,
            key="coach_exercise_choice_label",
            disabled=busy,
            index=labels.index(current_label),
        )
        exercise = label_map[selected]
        st.session_state.exercise_choice = exercise

    load_kg = st.number_input(
        TEXT["inputs"]["load"],
        min_value=0.0,
        step=2.5,
        key="ui_load_kg",
        disabled=busy,
    )
    upload_key = f"chat_video_upload_{int(st.session_state.get('chat_upload_nonce', 0))}"
    upload = st.file_uploader(
        TEXT["inputs"]["upload"],
        type=["mp4", "mov", "avi", "mkv", "webm"],
        key=upload_key,
        disabled=busy,
    )
    prompt = st.text_area(
        TEXT["chat"]["follow_up"],
        key="coach_followup_draft",
        height=96,
        disabled=busy,
        placeholder=(
            "Upload a new set to compare against the last one, or ask about a rep, cue, tempo, or next-step fix."
            if has_analysis else
            "Upload your first set and optionally add context for the coach."
        ),
        label_visibility="collapsed",
    )
    action_label = (
        "Analyze uploaded set"
        if upload is not None else
        ("Send follow-up" if has_analysis else TEXT["inputs"]["analyze"])
    )
    if st.button(
        action_label,
        key="coach_workspace_submit",
        use_container_width=True,
        type="primary",
        disabled=busy,
    ):
        if upload is not None:
            on_analyze(
                exercise,
                load_kg if load_kg > 0 else None,
                upload,
                prompt.strip(),
            )
        elif has_analysis and prompt.strip():
            on_followup(prompt.strip(), load_kg)
        elif not has_analysis:
            return ("warning", TEXT["inputs"]["upload_warning"])
        else:
            return ("info", "Add a follow-up question or upload another video for comparison.")

    return None


def _render_coach_notices(local_notice: tuple[str, str] | None) -> None:
    if local_notice:
        render_callout(local_notice[0], local_notice[1])

    notice = st.session_state.get("chat_upload_notice")
    if isinstance(notice, dict) and notice.get("text"):
        render_callout(notice.get("kind", "warning"), notice.get("text", ""))


def _render_coach_context_card(*, has_analysis: bool, has_response: bool) -> None:
    if has_analysis or has_response:
        with st.chat_message("assistant"):
            _coach_summary_card()
            action_cols = st.columns([1, 1])
            with action_cols[0]:
                open_analysis = st.button(
                    "Open analysis",
                    key="open_analysis_dialog",
                    use_container_width=True,
                )
            with action_cols[1]:
                p = artifact_analysis_json_path(st.session_state.get("last_analysis"))
                if p:
                    st.download_button(
                        "Export JSON",
                        data=p.read_text(encoding="utf-8"),
                        file_name=p.name,
                        mime="application/json",
                        use_container_width=True,
                        key="download_analysis_dialog_button",
                    )
            if open_analysis:
                _render_analysis_dialog()
        return

    with st.chat_message("assistant"):
        _coach_welcome_card()


def _render_coach_history() -> None:
    st.markdown(
        """<div class="rr-coach-history-intro">
            <div class="rr-section-kicker">Conversation</div>
            <div class="rr-coach-history-intro__title">Latest exchange</div>
            <div class="rr-coach-history-intro__copy">Your uploads, follow-ups, and coach replies stay here for the current session.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    chat_scroll = st.container(height=460)
    with chat_scroll:
        if not st.session_state.history:
            render_empty_state(EMPTY_STATES["chat"])
        for msg in st.session_state.history:
            role = "user" if msg.get("role") == "user" else "assistant"
            with st.chat_message(role):
                st.write(msg.get("content", ""))
                ts = msg.get("timestamp")
                if ts:
                    st.caption(ts[:16].replace("T", " "))


def render_coach_workspace(on_analyze: AnalyzeCallback, on_followup: FollowupCallback) -> None:
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
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
=======

        local_notice = _render_coach_composer(
            on_analyze,
            on_followup,
            busy=busy,
            has_analysis=has_analysis,
            exercise_locked=exercise_locked,
        )
        _render_coach_notices(local_notice)
        _render_coach_context_card(has_analysis=has_analysis, has_response=has_response)
        _render_coach_history()
>>>>>>> Stashed changes




