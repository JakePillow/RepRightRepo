from __future__ import annotations
from collections.abc import Callable
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import streamlit as st
from ui.components.primitives import (
    render_callout, render_empty_state, render_empty_state_results,
    render_quality_badge,
)
from ui.config.tokens import EMPTY_STATES, EXERCISES, EXERCISE_ICONS, TEXT
from ui.view_models import (
    artifact_analysis_json_path, comparison_view_model, quality_view_model, summary_metrics, top_fault_rows,
)

AnalyzeCallback  = Callable[[str, float | None, object, str], None]
FollowupCallback = Callable[[str, float], None]


def render_analysis_controls(on_analyze: AnalyzeCallback) -> None:
    busy = bool(st.session_state.get("ui_busy"))
    analysis = st.session_state.last_analysis
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
    else:
        labels    = [f"{EXERCISE_ICONS.get(e,'')} {e.capitalize()}" for e in EXERCISES]
        label_map = dict(zip(labels, EXERCISES))
        chosen    = st.selectbox(TEXT["inputs"]["exercise"], labels,
                                 key="exercise_choice_label", disabled=busy)
        exercise  = label_map[chosen]
        st.session_state.exercise_choice = exercise

    load_kg = st.number_input(TEXT["inputs"]["load"], min_value=0.0,
                               step=2.5, key="ui_load_kg", disabled=busy)
    upload  = st.file_uploader(TEXT["inputs"]["upload"],
                                type=["mp4", "mov", "avi", "mkv", "webm"],
                                key="uploaded_video", disabled=busy)
    note    = st.text_input(TEXT["inputs"]["coach_note"], key="coach_note_input", disabled=busy)

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
        f"<div class='rr-section-kicker' style='margin:20px 0 10px;'>{TEXT['recent_sessions_title']}</div>",
        unsafe_allow_html=True,
    )
    for thread in threads[:5]:
        title = thread.get("title") or thread.get("thread_id", "")
        st.markdown(
            f"""<div class="rr-session-row">
                <span>{title}</span>
                <span class="rr-session-row__arrow">›</span>
            </div>""",
            unsafe_allow_html=True,
        )


def _probe_video_stream(src: Path) -> tuple[str | None, str | None]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None, None

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,pix_fmt",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logging.warning("[FFPROBE FAILED] %s", proc.stderr.strip()[:240])
        return None, None

    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    codec = lines[0] if len(lines) >= 1 else None
    pix_fmt = lines[1] if len(lines) >= 2 else None
    return codec, pix_fmt


def _transcode_to_browser_mp4(src: Path) -> bytes | None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return None

    tmp_handle = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_handle.close()
    tmp_path = Path(tmp_handle.name)
    try:
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(src),
            "-map", "0:v:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(tmp_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logging.warning("[REENCODE FAILED] %s", proc.stderr.strip()[:240])
            return None
        if not tmp_path.exists() or tmp_path.stat().st_size <= 1000:
            return None
        return tmp_path.read_bytes()
    except Exception as exc:
        logging.warning("[REENCODE FAILED] %s", exc)
        return None
    finally:
        tmp_path.unlink(missing_ok=True)


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        p = Path(str(overlay_path))
        if p.exists() and p.stat().st_size > 0:
            suffix = p.suffix.lower()
            codec, pix_fmt = _probe_video_stream(p)
            logging.warning(
                "[OVERLAY PANEL] path='%s' suffix='%s' codec='%s' pix_fmt='%s' size=%s",
                p,
                suffix,
                codec,
                pix_fmt,
                p.stat().st_size,
            )

            if suffix == ".webm":
                st.video(p.read_bytes(), format="video/webm")
            elif suffix == ".mp4" and codec == "h264" and (pix_fmt is None or "420" in pix_fmt):
                st.video(p.read_bytes(), format="video/mp4")
            else:
                video_bytes = _transcode_to_browser_mp4(p)
                if video_bytes:
                    st.video(video_bytes, format="video/mp4")
                elif suffix == ".mp4":
                    st.video(p.read_bytes(), format="video/mp4")
                elif suffix == ".webm":
                    st.video(p.read_bytes(), format="video/webm")
                else:
                    st.warning(f"Overlay video could not be transcoded for browser playback: {p.name}")
                    render_empty_state_results()
        else:
            st.warning(f"Overlay file not found or empty at: {p}")
            render_empty_state_results()
    else:
        if st.session_state.get("last_analysis") or st.session_state.get("last_payload"):
            st.warning("Overlay artifact could not be resolved for this analysis.")
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
                f"""<div class="rr-metric-card">
                    <div class="rr-metric-card__label">{m.label}</div>
                    <div class="rr-metric-card__value">{m.value}</div>
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
                f"""<div class="rr-fault-row">{row}</div>""",
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
    busy = bool(st.session_state.get("ui_busy"))
    has_analysis = bool(st.session_state.get("last_analysis"))
    has_response = bool(st.session_state.get("last_response"))
    exercise_locked = bool(has_analysis and (st.session_state.get("last_analysis") or {}).get("exercise"))

    if st.session_state.get("clear_followup_draft_pending"):
        st.session_state.coach_followup_draft = ""
        st.session_state.clear_followup_draft_pending = False

    with st.container(border=True):
        st.markdown(
            """<div class="rr-coach-shell-head">
                <div>
                    <div class="rr-section-kicker">Coach Workspace</div>
                    <div class="rr-coach-shell-head__title">Chat With RepRight</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

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




