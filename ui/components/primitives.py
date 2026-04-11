from __future__ import annotations
from typing import Callable

import streamlit as st

from ui.config.tokens import THEME


def render_section(enabled: bool, body: Callable[[], None]) -> None:
    if enabled:
        body()


def render_quality_badge(title, score, color, zone_label, bg="#f1f5f9", ring="#cbd5e1") -> None:
    value = score if score is not None else "—"
    pct   = score if isinstance(score, int) else 0
    r     = 42
    circ  = 263.9
    dash  = circ * pct / 100
    st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    text-align:center;padding:28px 20px 22px;
                    border-radius:20px;background:{THEME['card_bg']};
                    border:1px solid {THEME['border']};
                    box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:14px;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;
                        color:{THEME['text_muted']};font-weight:700;margin-bottom:16px;">{title}</div>
            <div style="position:relative;width:110px;height:110px;margin-bottom:14px;">
                <svg width="110" height="110" viewBox="0 0 110 110">
                    <circle cx="55" cy="55" r="{r}" fill="none" stroke="{ring}" stroke-width="8"/>
                    <circle cx="55" cy="55" r="{r}" fill="none" stroke="{color}" stroke-width="8"
                        stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}"
                        transform="rotate(-90 55 55)"/>
                </svg>
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;">
                    <div style="font-size:30px;font-weight:900;color:{color};line-height:1;">{value}</div>
                    <div style="font-size:10px;color:{THEME['text_muted']};margin-top:2px;">/100</div>
                </div>
            </div>
            <div style="background:{color}18;color:{color};border:1.5px solid {color}44;
                        border-radius:999px;padding:4px 18px;
                        font-size:13px;font-weight:700;">{zone_label}</div>
        </div>""", unsafe_allow_html=True)


def render_empty_state(message: str) -> None:
    st.markdown(f"""
        <div style="padding:48px 24px;text-align:center;border-radius:16px;
                    background:{THEME['card_bg_alt']};border:1px solid {THEME['border']};color:{THEME['text_muted']};
                    font-size:14px;line-height:1.7;">
            <div style="font-size:36px;margin-bottom:12px;">📷</div>
            {message}
        </div>""", unsafe_allow_html=True)


def render_empty_state_results() -> None:
    from ui.config.tokens import TEXT
    t = TEXT["states"]
    st.markdown(f"""
        <div style="padding:52px 32px;text-align:center;border-radius:16px;
                    background:{THEME['card_bg_alt']};border:1px solid {THEME['border']};margin:4px 0;">
            <div style="font-size:40px;margin-bottom:14px;">📷</div>
            <div style="font-size:17px;font-weight:700;color:{THEME['text']};margin-bottom:8px;">
                {t["empty_title"]}</div>
            <div style="font-size:14px;color:{THEME['text_muted']};max-width:42ch;
                        margin:0 auto;line-height:1.7;">{t["empty_body"]}</div>
        </div>""", unsafe_allow_html=True)


def render_callout(kind: str, message: str) -> None:
    palette = {
        "warning": (THEME["warning"], THEME["warning_bg"], "⚠"),
        "success": (THEME["success"], THEME["success_bg"], "✓"),
        "info":    (THEME["accent"], THEME["accent_soft"], "ℹ"),
        "error":   (THEME["error"], THEME["error_bg"], "✕"),
    }
    color, bg, icon = palette.get(kind, palette["info"])
    st.markdown(f"""
        <div style="background:{bg};border:1.5px solid {color}44;border-radius:12px;
                    padding:12px 16px;margin:8px 0;color:{color};
                    font-size:14px;font-weight:500;display:flex;gap:10px;">
            <span>{icon}</span><span>{message}</span>
        </div>""", unsafe_allow_html=True)

def render_restore_status_badge(status: str | None) -> None:
    """
    Shows a subtle callout when a thread was restored with partial or missing data.
    Hidden entirely when status is None (fresh session) or 'full'.
    """
    if status in (None, "full"):
        return

    cfg = {
        "partial": (
            THEME["warning"], THEME["warning_bg"],
            "Partial restore",
            "This session is using a saved snapshot. Metrics are still available, but overlay or analysis files may be missing.",
        ),
        "missing": (
            THEME["error"], THEME["error_bg"],
            "Degraded restore",
            "Analysis artifacts could not be found. Re-upload the video to regenerate the overlay and full metrics.",
        ),
    }.get(status, (
        THEME["text_muted"], THEME["card_bg_alt"],
        "Unknown restore state",
        "Session state could not be fully verified.",
    ))

    color, bg, label, msg = cfg
    import streamlit as st
    st.markdown(
        f"""<div style="background:{bg};border:1.5px solid {color}44;
            border-radius:12px;padding:11px 16px;margin:0 0 14px;
            display:flex;gap:10px;align-items:flex-start;font-size:13px;">
            <span style="font-weight:700;color:{color};flex-shrink:0;">⚠ {label}</span>
            <span style="color:{THEME['text_soft']};">{msg}</span>
        </div>""",
        unsafe_allow_html=True,
    )
