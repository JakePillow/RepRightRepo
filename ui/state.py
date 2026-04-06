from __future__ import annotations

from typing import Any

import streamlit as st

SESSION_DEFAULTS: dict[str, Any] = {
    "thread_id": None,
    "thread_created_at": None,
    "thread_title": None,
    "exercise_choice": "bench",
    "ui_load_kg": 0.0,
    "history": [],
    "last_analysis": None,
    "last_payload": None,
    "last_response": None,
}


SESSION_GROUPS: dict[str, tuple[str, ...]] = {
    "analysis": ("last_analysis", "last_payload", "last_response"),
    "chat": ("history",),
}


def initialize_session_state() -> None:
    for key, default in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = list(default) if isinstance(default, list) else default


def reset_group(group_name: str) -> None:
    keys = SESSION_GROUPS.get(group_name, ())
    for key in keys:
        default = SESSION_DEFAULTS.get(key)
        st.session_state[key] = list(default) if isinstance(default, list) else default


def append_history(role: str, content: str, timestamp: str) -> None:
    st.session_state.history.append({"role": role, "content": content, "ts": timestamp})
