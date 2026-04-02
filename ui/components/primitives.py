from __future__ import annotations

from typing import Callable
import streamlit as st


def render_section(enabled: bool, body: Callable[[], None]) -> None:
    if enabled:
        body()


def render_quality_badge(
    title: str,
    score: int | None,
    color: str,
    zone_label: str,
    bg: str = "#1f2937",
    ring: str = "#374151",
) -> None:
    value = score if score is not None else "n/a"
    st.markdown(
        f"""
        <div style="
            display:flex; align-items:center; justify-content:space-between;
            gap:16px; padding:18px 20px; border-radius:18px;
            border:1px solid rgba(255,255,255,0.08);
            background: linear-gradient(135deg, {bg}cc, {bg}66);
            margin-bottom:8px;
        ">
            <div>
                <div style="font-size:11px; text-transform:uppercase;
                            letter-spacing:0.09em; color:#9ca3af;">{title}</div>
                <div style="
                    display:inline-block; margin-top:6px;
                    background:{color}22; color:{color};
                    border:1px solid {color}55; border-radius:999px;
                    padding:3px 14px; font-size:13px; font-weight:600;
                ">{zone_label}</div>
            </div>
            <div style="
                width:72px; height:72px; border-radius:50%;
                border:3px solid {ring};
                box-shadow: 0 0 0 3px {color}33;
                display:flex; align-items:center; justify-content:center;
                flex-shrink:0;
            ">
                <span style="font-size:26px; font-weight:700; color:{color};">{value}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(message: str) -> None:
    st.markdown(
        f"""
        <div style="
            padding:36px 20px; text-align:center;
            border:1px solid rgba(255,255,255,0.07);
            border-radius:16px;
            background:rgba(255,255,255,0.02);
            color:#6b7280; font-size:14px; line-height:1.6;
            margin:4px 0;
        ">{message}</div>
        """,
        unsafe_allow_html=True,
    )


def render_callout(kind: str, message: str) -> None:
    palette = {
        "warning": ("#f59e0b", "#451a03", "⚠"),
        "success": ("#10b981", "#064e3b", "✓"),
        "info":    ("#60a5fa", "#1e3a5f", "ℹ"),
    }
    color, bg, icon = palette.get(kind, palette["info"])
    st.markdown(
        f"""
        <div style="
            background:{bg}; border:1px solid {color}44;
            border-radius:10px; padding:12px 16px; margin:8px 0;
            color:{color}; font-size:14px;
            display:flex; gap:10px; align-items:flex-start;
        ">
            <span style="flex-shrink:0;">{icon}</span>
            <span>{message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
