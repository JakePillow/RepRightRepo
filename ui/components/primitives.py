from __future__ import annotations

from typing import Callable

import streamlit as st


def render_section(enabled: bool, body: Callable[[], None]) -> None:
    if enabled:
        body()


def render_quality_badge(title: str, score: int | None, color: str, zone_label: str) -> None:
    value = score if score is not None else "n/a"
    st.markdown(
        f"### {title}: <span style='color:{color};'>**{value}**</span> ({zone_label})",
        unsafe_allow_html=True,
    )


def render_empty_state(message: str) -> None:
    st.caption(message)


def render_callout(kind: str, message: str) -> None:
    if kind == "warning":
        st.warning(message)
    elif kind == "success":
        st.success(message)
    else:
        st.info(message)
