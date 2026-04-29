from __future__ import annotations
from collections.abc import Callable
import json
import logging
import shutil
import subprocess
from pathlib import Path

import streamlit as st
from repright.llm_wrapper import format_response_text
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
    from ui.chat_store import list_threads, load_thread
    threads = list_threads()
    if not threads:
        st.markdown(
            """<div class="rr-mini-empty">
                No saved sessions yet. Once you analyze a set, the latest sessions will appear here for quick recall.
            </div>""",
            unsafe_allow_html=True,
        )
        return
    for thread in threads[:5]:
        tid = thread.get("thread_id")
        title = thread.get("title") or tid or "Untitled session"
        if st.button(
            f"{title}  ›",
            key=f"main_recent_{tid}",
            use_container_width=True,
            type="tertiary",
        ):
            if tid:
                load_thread(tid)
                st.rerun()


def _probe_video_stream(src: Path) -> tuple[str | None, str | None, int]:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return None, None, 0

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,pix_fmt:stream_tags=rotate:stream_side_data=rotation",
        "-of", "json",
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logging.warning("[FFPROBE FAILED] %s", proc.stderr.strip()[:240])
        return None, None, 0

    try:
        payload = json.loads(proc.stdout or "{}")
        stream = (payload.get("streams") or [{}])[0]
    except Exception:
        logging.warning("[FFPROBE PARSE FAILED] Could not decode probe output for %s", src)
        return None, None, 0

    codec = stream.get("codec_name")
    pix_fmt = stream.get("pix_fmt")
    rotation = 0

    tags = stream.get("tags") or {}
    if tags.get("rotate") is not None:
        try:
            rotation = int(float(tags.get("rotate")))
        except Exception:
            rotation = 0

    for entry in stream.get("side_data_list") or []:
        raw = entry.get("rotation")
        if raw is None:
            continue
        try:
            rotation = int(float(raw))
            break
        except Exception:
            continue

    return codec, pix_fmt, rotation % 360


def _browser_ready_overlay_path(src: Path) -> Path:
    return src.with_name(f"{src.stem}_browser.mp4")


def _rotation_filter(rotation: int) -> str | None:
    normalized = rotation % 360
    if normalized == 90:
        return "transpose=1"
    if normalized == 180:
        return "hflip,vflip"
    if normalized == 270:
        return "transpose=2"
    return None


def _transcode_to_browser_mp4(src: Path, dst: Path, *, rotation: int = 0) -> Path | None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        return None

    dst.parent.mkdir(parents=True, exist_ok=True)
    filters: list[str] = []
    rotation_filter = _rotation_filter(rotation)
    if rotation_filter:
        filters.append(rotation_filter)
    filters.extend(["format=yuv420p", "setsar=1"])
    try:
        cmd = [
            ffmpeg,
            "-y",
            "-noautorotate",
            "-i", str(src),
            "-map", "0:v:0",
            "-metadata:s:v:0", "rotate=0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", ",".join(filters),
            "-movflags", "+faststart",
            str(dst),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            logging.warning("[REENCODE FAILED] %s", proc.stderr.strip()[:240])
            return None
        if not dst.exists() or dst.stat().st_size <= 50 * 1024:
            return None
        return dst
    except Exception as exc:
        logging.warning("[REENCODE FAILED] %s", exc)
        return None


def _ensure_browser_ready_overlay(src: Path) -> Path | None:
    codec, pix_fmt, rotation = _probe_video_stream(src)
    cache_path = _browser_ready_overlay_path(src)

    if cache_path.exists():
        try:
            if cache_path.stat().st_size > 50 * 1024 and cache_path.stat().st_mtime >= src.stat().st_mtime:
                return cache_path
        except OSError:
            pass

    if src.suffix.lower() == ".mp4" and codec == "h264" and (pix_fmt is None or "420" in pix_fmt) and rotation == 0:
        return src

    return _transcode_to_browser_mp4(src, cache_path, rotation=rotation)


def render_overlay_panel(overlay_path) -> None:
    if overlay_path:
        p = Path(str(overlay_path))
        if p.exists() and p.stat().st_size > 0:
            suffix = p.suffix.lower()
            codec, pix_fmt, rotation = _probe_video_stream(p)
            logging.debug(
                "[OVERLAY PANEL] path='%s' suffix='%s' codec='%s' pix_fmt='%s' rotation='%s' size=%s",
                p,
                suffix,
                codec,
                pix_fmt,
                rotation,
                p.stat().st_size,
            )

            browser_ready = _ensure_browser_ready_overlay(p)
            if browser_ready is not None:
                analysis = st.session_state.get("last_analysis")
                if isinstance(analysis, dict):
                    artifacts = analysis.setdefault("artifacts_v1", {})
                    artifacts["browser_overlay_path"] = str(browser_ready.resolve())
                st.video(str(browser_ready), format="video/mp4" if browser_ready.suffix.lower() == ".mp4" else "video/webm")
            elif suffix == ".webm":
                st.video(str(p), format="video/webm")
            elif suffix == ".mp4":
                st.video(str(p), format="video/mp4")
            else:
                st.warning(f"Overlay video could not be prepared for browser playback: {p.name}")
                render_empty_state_results()
        else:
            st.warning(f"Overlay file not found or empty at: {p}")
            render_empty_state_results()
    else:
        if st.session_state.get("last_analysis") or st.session_state.get("last_payload"):
            st.warning("Overlay artifact could not be resolved for this analysis.")
        render_empty_state_results()


def render_quality_header(*, variant: str = "default") -> None:
    vm = quality_view_model(st.session_state.last_analysis, st.session_state.last_response)
    if variant == "hero":
        st.markdown('<div class="rr-analysis-badge-hero-shell"></div>', unsafe_allow_html=True)
    render_quality_badge(
        TEXT["results"]["quality_title"],
        vm.score,
        vm.color,
        vm.zone_label,
        bg=vm.bg,
        ring=vm.ring,
    )


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
    response = st.session_state.get("last_response") or {}
    exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "analysis").capitalize()
    reps = summary.get("n_reps", "—")
    avg_rom = summary.get("avg_rom")
    avg_rom_label = f"{float(avg_rom):.2f}" if isinstance(avg_rom, (int, float)) else "n/a"
    load_kg = st.session_state.get("ui_load_kg")
    load_label = f"{float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "Load: n/a"
    quality_vm = quality_view_model(analysis, response)

    summary_col, badge_col = st.columns([1.7, 0.9], gap="medium")
    with summary_col:
        st.markdown(
            f"""<div class="rr-summary-strip">
                <div class="rr-summary-strip__main">
                    <div class="rr-kicker rr-kicker--light">Latest analysis</div>
                    <div class="rr-summary-strip__title">{exercise}</div>
                    <div class="rr-summary-strip__copy">
                        {reps} reps detected. Average ROM {avg_rom_label}. {load_label}.
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    with badge_col:
        render_quality_badge(
            TEXT["results"]["quality_title"],
            quality_vm.score,
            quality_vm.color,
            quality_vm.zone_label,
            bg=quality_vm.bg,
            ring=quality_vm.ring,
        )

    if compare_vm and compare_vm.metrics:
        chips = "".join(
            f"""<span class="rr-chip rr-chip--compare rr-chip--compare-{metric.tone}">
                {metric.label} change: {metric.delta}
            </span>"""
            for metric in compare_vm.metrics[:4]
        )
        st.markdown(
            f"""<div class="rr-summary-strip rr-summary-strip--comparison">
                <div class="rr-summary-strip__main">
                    <div class="rr-kicker rr-kicker--light">Comparison</div>
                    <div class="rr-summary-strip__copy">{compare_vm.summary}</div>
                </div>
                <div class="rr-chip-row rr-chip-row--compact">{chips}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _coach_welcome_card() -> None:
    t = TEXT["coaching_panel"]
    steps = "".join(
        f"""<div class="rr-workspace-hint__step">
            <div class="rr-workspace-hint__icon">{icon}</div>
            <div class="rr-workspace-hint__step-copy">
                <div class="rr-workspace-hint__step-title">{title}</div>
                <div class="rr-workspace-hint__step-desc">{desc}</div>
            </div>
        </div>"""
        for icon, title, desc in t["steps"]
    )
    st.markdown(
        f"""<div class="rr-workspace-hint">
            <div class="rr-kicker rr-kicker--light">Coach Workflow</div>
            <div class="rr-workspace-hint__title">{t['title']}</div>
            <div class="rr-workspace-hint__copy">
                Upload one clear side-view set to open the replay, movement metrics, and the coaching thread.
            </div>
            <div class="rr-workspace-hint__grid">{steps}</div>
            <div class="rr-workspace-hint__tip">{t['tip']}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_analysis_dialog() -> None:
    @st.dialog("Analysis Snapshot", width="large")
    def _analysis_dialog() -> None:
        analysis = st.session_state.get("last_analysis") or {}
        response = st.session_state.get("last_response") or {}
        exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "analysis").capitalize()
        summary = analysis.get("set_summary_v1") or {}
        load_kg = st.session_state.get("ui_load_kg")
        load_label = f"{float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "n/a"
        response_text = format_response_text(response, st.session_state.get("last_payload") or {})
        reps = summary.get("n_reps", "—")
        fault_count = len(top_fault_rows(summary))

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

        st.markdown('<div class="rr-analysis-overview-shell"></div>', unsafe_allow_html=True)
        overview_col, metrics_col = st.columns([0.98, 1.7], gap="large")
        with overview_col:
            render_quality_header(variant="hero")
        with metrics_col:
            st.markdown(
                f"""<div class="rr-analysis-overview-copy">
                    <div class="rr-analysis-overview-copy__kicker">Analysis snapshot</div>
                    <div class="rr-analysis-overview-copy__title">{exercise} overview</div>
                    <div class="rr-analysis-overview-copy__body">
                        {reps} reps detected at {load_label}. {fault_count} flagged issue{"s" if fault_count != 1 else ""} surfaced in this set.
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            render_summary_metrics()

        render_comparison_panel()
        render_faults_panel()
        render_artifacts_panel()

        if response_text:
            with st.container():
                st.markdown('<div class="rr-analysis-reply-shell"></div>', unsafe_allow_html=True)
                st.markdown(
                    """<div class="rr-section-kicker" style="margin-bottom:8px;">Latest Coach Reply</div>""",
                    unsafe_allow_html=True,
                )
                st.markdown(response_text)

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
        "Upload the next clip to compare it, or send a quick follow-up below."
        if has_analysis else
        "Choose the lift, add the load if it matters, then upload the set."
    )
    title = (
        "Compare the next set or ask a follow-up"
        if has_analysis else
        "Start a set review"
    )

    with st.container():
        st.markdown('<div class="rr-analysis-bar-shell"></div>', unsafe_allow_html=True)
        st.markdown(
            f"""<div class="rr-analysis-bar-head">
                <div class="rr-section-kicker">Session Input</div>
                <div class="rr-analysis-bar-head__title">{title}</div>
                <div class="rr-analysis-bar-head__copy">{caption}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        exercise_col, load_col = st.columns([1.45, 0.75], gap="small")
        with exercise_col:
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

        with load_col:
            load_kg = st.number_input(
                TEXT["inputs"]["load"],
                min_value=0.0,
                step=2.5,
                key="ui_load_kg",
                disabled=busy,
            )

        upload_key = f"chat_video_upload_{int(st.session_state.get('chat_upload_nonce', 0))}"
        upload_col, prompt_col = st.columns([1.05, 1], gap="small")
        with upload_col:
            upload = st.file_uploader(
                TEXT["inputs"]["upload"],
                type=["mp4", "mov", "avi", "mkv", "webm"],
                key=upload_key,
                disabled=busy,
            )
        with prompt_col:
            prompt = st.text_area(
                TEXT["chat"]["follow_up"],
                key="coach_followup_draft",
                height=110,
                disabled=busy,
                placeholder=(
                    "Ask about a rep, cue, tempo, or what to change next."
                    if has_analysis else
                    "Optional context for the coach."
                ),
                label_visibility="collapsed",
            )

        action_label = (
            ("Compare this set" if has_analysis else "Run analysis")
            if upload is not None else
            ("Ask coach" if has_analysis else "Run analysis")
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
    with st.container():
        st.markdown('<div class="rr-context-shell"></div>', unsafe_allow_html=True)
        if has_analysis or has_response:
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

        _coach_welcome_card()


def _render_coach_history() -> None:
    with st.container():
        st.markdown('<div class="rr-history-shell"></div>', unsafe_allow_html=True)
        st.markdown(
            """<div class="rr-history-head">
                <div class="rr-section-kicker">Conversation</div>
                <div class="rr-history-head__title">Coach thread</div>
                <div class="rr-history-head__copy">Keep uploads, follow-ups, and replies in one running conversation.</div>
            </div>""",
            unsafe_allow_html=True,
        )

        chat_scroll = st.container()
        with chat_scroll:
            if not st.session_state.history:
                render_empty_state(EMPTY_STATES["chat"])
            for msg in st.session_state.history:
                role = "user" if msg.get("role") == "user" else "assistant"
                with st.chat_message(role):
                    st.markdown(str(msg.get("content", "")))
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

    with st.container():
        st.markdown('<div class="rr-coach-workspace-shell"></div>', unsafe_allow_html=True)
        st.markdown(
            """<div class="rr-coach-shell-head">
                <div>
                    <div class="rr-section-kicker">Coach Workspace</div>
                    <div class="rr-coach-shell-head__title">Coach Thread</div>
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



