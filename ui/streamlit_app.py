from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from repright.analyzer import RepRightAnalyzer
from repright.coach_payload import build_coach_payload
from repright.llm_wrapper import run_coach


EXERCISES = ["bench", "deadlift", "squat", "curl"]

CHATS_DIR = ROOT / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_thread_id(exercise: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{exercise}"


def _thread_path(thread_id: str) -> Path:
    return CHATS_DIR / f"{thread_id}.json"


def _parse_ts(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min


def list_threads() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    for p in CHATS_DIR.glob("*.json"):
        try:
            thread = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(thread, dict):
                out.append(thread)
        except Exception:
            continue

    out.sort(key=lambda t: _parse_ts(t.get("updated_at")), reverse=True)
    return out


def _thread_title(created_at: str | None, exercise: str | None) -> str:
    ex = exercise or "unknown"

    try:
        dt = datetime.fromisoformat(created_at or "")
        return f"{dt.strftime('%Y-%m-%d')} - {ex}"
    except ValueError:
        return f"{datetime.now().strftime('%Y-%m-%d')} - {ex}"


def _save_thread(thread_id: str) -> None:
    if not thread_id:
        return

    analysis = st.session_state.get("last_analysis") or {}
    artifacts = analysis.get("artifacts_v1") if isinstance(analysis.get("artifacts_v1"), dict) else {}

    analysis_json = artifacts.get("analysis_json") or analysis.get("metrics_path")
    overlay_path = analysis.get("overlay_path") or artifacts.get("overlay_path")

    fallback_exercise = analysis.get("exercise") or st.session_state.get("exercise_choice") or thread_id.split("_")[-1]

    thread = {
        "thread_id": thread_id,
        "created_at": st.session_state.get("thread_created_at"),
        "updated_at": _now_iso(),
        "title": st.session_state.get("thread_title") or _thread_title(st.session_state.get("thread_created_at"), fallback_exercise),
        "exercise": fallback_exercise,
        "analysis_ref": {
            "analysis_json": analysis_json,
            "overlay_path": overlay_path,
            "run_dir": artifacts.get("run_dir"),
        },
        "history": st.session_state.get("history") or [],
    }

    _thread_path(thread_id).write_text(json.dumps(thread, indent=2), encoding="utf-8")


def _load_thread(thread_id: str) -> None:
    p = _thread_path(thread_id)

    if not p.exists():
        return

    thread = json.loads(p.read_text(encoding="utf-8"))
    analysis_ref = thread.get("analysis_ref") if isinstance(thread.get("analysis_ref"), dict) else {}

    st.session_state.thread_id = thread.get("thread_id")
    st.session_state.thread_created_at = thread.get("created_at")
    st.session_state.thread_title = thread.get("title")
    st.session_state.exercise_choice = thread.get("exercise") or "bench"

    st.session_state.history = thread.get("history") if isinstance(thread.get("history"), list) else []

    analysis_json = analysis_ref.get("analysis_json")

    loaded_analysis: dict[str, Any] | None = None

    if analysis_json:
        p_analysis = Path(str(analysis_json))

        if p_analysis.exists():
            try:
                loaded_analysis = json.loads(p_analysis.read_text(encoding="utf-8"))
            except Exception:
                loaded_analysis = None

    if loaded_analysis is None:
        loaded_analysis = {
            "exercise": thread.get("exercise"),
            "overlay_path": analysis_ref.get("overlay_path"),
            "artifacts_v1": {
                "analysis_json": analysis_json,
                "overlay_path": analysis_ref.get("overlay_path"),
                "run_dir": analysis_ref.get("run_dir"),
                "metrics_path": analysis_json,
            },
        }

    st.session_state.last_analysis = loaded_analysis
    st.session_state.last_payload = None
    st.session_state.last_response = None


def _append_history(role: str, content: str) -> None:
    st.session_state.history.append({"role": role, "content": content, "ts": _now_iso()})


def _safe_tmp_video(upload) -> Path:
    suffix = Path(upload.name).suffix or ".mp4"
    fd, path = tempfile.mkstemp(prefix="repright_", suffix=suffix)
    os.close(fd)

    p = Path(path)
    p.write_bytes(upload.getbuffer())

    return p


def _resolve_overlay_path() -> Path | None:
    payload = st.session_state.last_payload or {}
    analysis = st.session_state.last_analysis or {}

    raw = [
        (payload.get("highlights") or {}).get("overlay_path"),
        (analysis.get("artifacts_v1") or {}).get("overlay_path") if isinstance(analysis, dict) else None,
        analysis.get("overlay_path") if isinstance(analysis, dict) else None,
    ]

    for c in raw:
        if not c:
            continue

        p = Path(str(c))

        try:
            if p.exists() and p.stat().st_size > 0:
                return p
        except Exception:
            pass

    return None


def _canonical_lift_quality(analysis: dict[str, Any] | None) -> int | None:
    if not isinstance(analysis, dict):
        return None

    summary = analysis.get("set_summary_v1")
    if not isinstance(summary, dict):
        return None

    score = summary.get("quality_score")
    if score is None:
        score = summary.get("quality_score_pct")

    return int(score) if isinstance(score, (int, float)) else None


def _quality_color(score: int | None) -> tuple[str, str]:
    if score is None:
        return "#8a8f98", "n/a"

    if score >= 80:
        return "#35d07f", "Green"

    if score >= 50:
        return "#f0c04f", "Yellow"

    return "#f25f5c", "Red"


def _run_pipeline(upload, exercise: str, user_message: str, load_kg: float | None):
    tmp_path = _safe_tmp_video(upload)

    prog = st.progress(0, text="Tracking pose...")

    analyzer = RepRightAnalyzer()

    analysis = analyzer.analyze(str(tmp_path), exercise)

    prog.progress(60, text="Building coach context...")

    payload = build_coach_payload(
        analysis,
        message=user_message,
        load_kg=load_kg,
        history=st.session_state.history[-6:],
    )

    prog.progress(85, text="Generating coaching response...")

    response = run_coach(payload)

    prog.progress(100, text="Done.")
    time.sleep(0.1)
    prog.empty()

    return analysis, payload, response


def _new_chat(exercise: str):
    thread_id = _new_thread_id(exercise)

    st.session_state.thread_id = thread_id
    st.session_state.thread_created_at = _now_iso()
    st.session_state.thread_title = _thread_title(st.session_state.thread_created_at, exercise)

    st.session_state.exercise_choice = exercise

    st.session_state.history = []
    st.session_state.last_analysis = None
    st.session_state.last_payload = None
    st.session_state.last_response = None

    _save_thread(thread_id)


st.set_page_config(page_title="RepRight", layout="wide")

for key in ["thread_id", "thread_created_at", "thread_title", "history", "last_analysis", "last_payload", "last_response"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "history" else None


if st.session_state.thread_id is None:
    _new_chat(st.session_state.get("exercise_choice") or "bench")


with st.sidebar:
    if st.button("+ New chat", use_container_width=True):
        _new_chat(st.session_state.get("exercise_choice") or "bench")
        st.rerun()

    st.markdown("### Chats")

    for thread in list_threads():
        tid = thread.get("thread_id")

        if st.button(thread.get("title") or tid, key=tid, use_container_width=True):
            _load_thread(tid)
            st.rerun()


left, right = st.columns([1.05, 0.95])


with left:
    exercise_locked = bool(st.session_state.last_analysis and st.session_state.last_analysis.get("exercise"))

    if exercise_locked:
        st.session_state.exercise_choice = st.session_state.last_analysis.get("exercise")

    exercise = st.selectbox("Exercise", EXERCISES, key="exercise_choice", disabled=exercise_locked)

    load_kg = st.number_input("Load (kg)", min_value=0.0, value=0.0)
    use_load = load_kg if load_kg > 0 else None

    upload = st.file_uploader("Upload set video", type=["mp4", "mov", "avi", "mkv"])

    user_message = st.text_input("Optional note to coach")

    if st.button("Analyze set", use_container_width=True):
        if upload is None:
            st.warning("Upload a video first.")
        else:
            analysis, payload, response = _run_pipeline(upload, exercise, user_message, use_load)

            st.session_state.last_analysis = analysis
            st.session_state.last_payload = payload
            st.session_state.last_response = response

            if user_message:
                _append_history("user", user_message)

            _append_history("assistant", response.get("response_text", ""))

            _save_thread(st.session_state.thread_id)

    overlay_path = _resolve_overlay_path()

    if overlay_path:
        st.video(str(overlay_path))


with right:
    structured = (st.session_state.last_response or {}).get("structured") if isinstance(st.session_state.last_response, dict) else {}

    score = structured.get("overall_score") if isinstance(structured, dict) else None

    if score is None:
        score = _canonical_lift_quality(st.session_state.last_analysis)

    color, zone = _quality_color(score)

    st.markdown(f"### Lift Quality: **{score if score is not None else 'n/a'}** ({zone})")

    for msg in st.session_state.history:
        role = "user" if msg.get("role") == "user" else "assistant"
        st.chat_message(role).write(msg.get("content"))

    follow = st.chat_input("Ask a follow-up...")

    if follow and st.session_state.last_analysis:
        payload = build_coach_payload(
            st.session_state.last_analysis,
            message=follow,
            load_kg=load_kg,
            history=st.session_state.history[-8:],
        )

        response = run_coach(payload)

        st.session_state.last_payload = payload
        st.session_state.last_response = response

        _append_history("user", follow)
        _append_history("assistant", response.get("response_text", ""))

        _save_thread(st.session_state.thread_id)

        st.rerun()
