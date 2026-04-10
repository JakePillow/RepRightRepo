from __future__ import annotations
from typing import Any
import streamlit as st

_DEFAULTS: dict[str, Any] = {
    "thread_id":         None,
    "thread_title":      "",
    "thread_created_at": "",
    "exercise_choice":   "bench",
    "history":           [],
    "last_analysis":     None,
    "last_payload":      None,
    "last_response":     None,
    "restore_status":    None,   # 'full' | 'partial' | 'missing' | None
}

_RESET_GROUPS: dict[str, list[str]] = {
    "chat":     ["history"],
    "analysis": ["last_analysis", "last_payload", "last_response", "restore_status"],
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
    st.session_state.history.append({
        "role":      role,
        "content":   content,
        "timestamp": timestamp,
    })
