from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
CHATS_DIR = ROOT / "data" / "chats"
CHATS_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_thread_id(exercise: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{exercise}"


def thread_path(thread_id: str) -> Path:
    return CHATS_DIR / f"{thread_id}.json"


def parse_ts(ts: str | None) -> datetime:
    if not ts:
        return datetime.min
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.min


def thread_title(created_at: str | None, exercise: str | None) -> str:
    ex = exercise or "unknown"
    try:
        dt = datetime.fromisoformat(created_at or "")
        return f"{dt.strftime('%Y-%m-%d')} - {ex}"
    except ValueError:
        return f"{datetime.now().strftime('%Y-%m-%d')} - {ex}"


def list_threads() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in CHATS_DIR.glob("*.json"):
        try:
            thread = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(thread, dict):
                out.append(thread)
        except Exception:
            continue

    out.sort(key=lambda t: parse_ts(t.get("updated_at")), reverse=True)
    return out


def save_thread(thread_id: str) -> None:
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
        "updated_at": now_iso(),
        "title": st.session_state.get("thread_title") or thread_title(st.session_state.get("thread_created_at"), fallback_exercise),
        "exercise": fallback_exercise,
        "analysis_ref": {
            "analysis_json": analysis_json,
            "overlay_path": overlay_path,
            "run_dir": artifacts.get("run_dir"),
        },
        "history": st.session_state.get("history") or [],
    }

    thread_path(thread_id).write_text(json.dumps(thread, indent=2), encoding="utf-8")


def load_thread(thread_id: str) -> None:
    p = thread_path(thread_id)
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
