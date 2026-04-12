from __future__ import annotations

from typing import Any

import streamlit as st

_DEFAULTS: dict[str, Any] = {
    "thread_id": None,
    "thread_title": "",
    "thread_created_at": "",
    "exercise_choice": "bench",
    "history": [],
    "last_analysis": None,
    "last_payload": None,
    "last_response": None,
    "restore_status": None,
    "ui_busy": False,
    "ui_message": None,
    "ui_load_kg": 0.0,
    "coach_note_input": "",
    "clear_coach_note_pending": False,
}

_RESET_GROUPS: dict[str, list[str]] = {
    "chat": ["history", "last_payload", "last_response"],
    "analysis": ["last_analysis", "last_payload", "last_response", "restore_status"],
    "thread": ["thread_id", "thread_title", "thread_created_at", "restore_status"],
}


def initialize_session_state() -> None:
    for key, default in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = (
                default.copy() if isinstance(default, (dict, list)) else default
            )


def reset_group(group: str) -> None:
    for key in _RESET_GROUPS.get(group, []):
        default = _DEFAULTS.get(key)
        st.session_state[key] = (
            default.copy() if isinstance(default, (dict, list)) else default
        )


def append_history(role: str, content: str, timestamp: str) -> None:
    st.session_state.history.append(
        {
            "role": role,
            "content": content,
            "timestamp": timestamp,
        }
    )


def set_ui_busy(is_busy: bool) -> None:
    st.session_state.ui_busy = bool(is_busy)


def set_ui_message(kind: str, text: str) -> None:
    st.session_state.ui_message = {"kind": kind, "text": text}


def clear_ui_message() -> None:
    st.session_state.ui_message = None


def reset_draft_session(exercise: str = "bench") -> None:
    reset_group("chat")
    reset_group("analysis")
    reset_group("thread")
    st.session_state.exercise_choice = exercise
    st.session_state.ui_load_kg = 0.0
    st.session_state.coach_note_input = ""
    st.session_state.clear_coach_note_pending = False
    st.session_state.ui_busy = False
    st.session_state.ui_message = None
    if "exercise_choice_label" in st.session_state:
        del st.session_state["exercise_choice_label"]
    if "uploaded_video" in st.session_state:
        del st.session_state["uploaded_video"]


def request_coach_note_clear() -> None:
    st.session_state.clear_coach_note_pending = True
