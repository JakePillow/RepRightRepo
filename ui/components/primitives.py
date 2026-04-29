from __future__ import annotations

from textwrap import dedent
from typing import Callable

import streamlit as st


def render_section(enabled: bool, body: Callable[[], None]) -> None:
    if enabled:
        body()


def _render_html(markup: str) -> None:
    html = dedent(markup).strip()
    if hasattr(st, "html"):
        st.html(html)
    else:
        st.markdown(html, unsafe_allow_html=True)


def _render_markdown_html(markup: str) -> None:
    st.markdown(dedent(markup).strip(), unsafe_allow_html=True)


def lift_loop_markup(*, compact: bool = False) -> str:
    compact_class = " rr-lift-loop--compact" if compact else ""
    return f"""
        <div class="rr-lift-loop{compact_class}" aria-hidden="true">
            <div class="rr-lift-loop__platform"></div>
            <div class="rr-lift-loop__barbell"></div>
            <div class="rr-lift-loop__plate rr-lift-loop__plate--left"></div>
            <div class="rr-lift-loop__plate rr-lift-loop__plate--right"></div>
            <div class="rr-lift-loop__athlete">
                <div class="rr-lift-loop__head"></div>
                <div class="rr-lift-loop__torso"></div>
                <div class="rr-lift-loop__arm rr-lift-loop__arm--left"></div>
                <div class="rr-lift-loop__arm rr-lift-loop__arm--right"></div>
                <div class="rr-lift-loop__leg rr-lift-loop__leg--left"></div>
                <div class="rr-lift-loop__leg rr-lift-loop__leg--right"></div>
            </div>
            <div class="rr-lift-loop__wave rr-lift-loop__wave--one"></div>
            <div class="rr-lift-loop__wave rr-lift-loop__wave--two"></div>
        </div>
    """


def render_quality_badge(
    title,
    score,
    color,
    zone_label,
    bg="#f1f5f9",
    ring="#cbd5e1",
    *,
    variant: str = "default",
) -> None:
    value = score if score is not None else "-"
    pct = float(score) if isinstance(score, (int, float)) else 0
    hero = variant == "hero"
    size = 152 if hero else 110
    center = size / 2
    radius = 58 if hero else 42
    stroke = 10 if hero else 8
    circ = 2 * 3.141592653589793 * radius
    dash = circ * pct / 100
    _render_markdown_html(
        f"""
        <div class="rr-glass-card rr-quality-badge rr-quality-badge--{variant}">
            <div class="rr-quality-badge__title">{title}</div>
            <div class="rr-quality-badge__ring">
                <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" aria-hidden="true">
                    <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{ring}" stroke-width="{stroke}"/>
                    <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke}"
                        stroke-linecap="round" stroke-dasharray="{dash:.1f} {circ:.1f}"
                        transform="rotate(-90 {center} {center})"/>
                </svg>
                <div class="rr-quality-badge__value-wrap">
                    <div class="rr-quality-badge__value" style="color:{color};">{value}</div>
                    <div class="rr-quality-badge__scale">/100</div>
                </div>
            </div>
            <div class="rr-quality-badge__zone" style="background:{bg};color:{color};border-color:{color}44;">{zone_label}</div>
        </div>
        """
    )


def render_empty_state(message: str) -> None:
    _render_html(
        f"""
        <div class="rr-empty-card">
            <div class="rr-empty-card__icon">&#128172;</div>
            <div class="rr-empty-card__body">{message}</div>
        </div>
        """
    )


def render_empty_state_results() -> None:
    from ui.config.tokens import TEXT

    t = TEXT["states"]
    _render_html(
        f"""
        <div class="rr-empty-card rr-empty-card--results">
            <div class="rr-empty-card__icon rr-empty-card__icon--large">&#127947;</div>
            <div class="rr-empty-card__title">{t["empty_title"]}</div>
            <div class="rr-empty-card__body">{t["empty_body"]}</div>
        </div>
        """
    )


def render_callout(kind: str, message: str) -> None:
    palette = {
        "warning": ("var(--rr-warning)", "var(--rr-warning-bg)", "!"),
        "success": ("var(--rr-success)", "var(--rr-success-bg)", "+"),
        "info": ("var(--rr-accent)", "var(--rr-accent-soft)", "i"),
        "error": ("var(--rr-error)", "var(--rr-error-bg)", "!"),
    }
    color, bg, icon = palette.get(kind, palette["info"])
    _render_html(
        f"""
        <div class="rr-callout" style="--rr-callout-color:{color};--rr-callout-bg:{bg};">
            <span class="rr-callout__icon">{icon}</span><span class="rr-callout__body">{message}</span>
        </div>
        """
    )


def render_restore_status_badge(status: str | None) -> None:
    """
    Shows a subtle callout when a thread was restored with partial or missing data.
    Hidden entirely when status is None (fresh session) or 'full'.
    """
    if status in (None, "full"):
        return

    cfg = {
        "partial": (
            "var(--rr-warning)",
            "var(--rr-warning-bg)",
            "Partial restore",
            "Some analysis metrics were reloaded from an embedded snapshot. "
            "Artifact files (overlay video) may no longer be available.",
        ),
        "missing": (
            "var(--rr-error)",
            "var(--rr-error-bg)",
            "Degraded restore",
            "Analysis artifacts could not be found. Metrics and faults shown "
            "may be unavailable. Re-upload the video to regenerate a full analysis.",
        ),
    }.get(
        status,
        (
            "var(--rr-text-muted)",
            "var(--rr-card-bg-alt)",
            "Unknown restore state",
            "Session state could not be fully verified.",
        ),
    )

    color, bg, label, msg = cfg
    _render_html(
        f"""
        <div class="rr-callout rr-callout--restore" style="--rr-callout-color:{color};--rr-callout-bg:{bg};margin:0 0 14px;">
            <span class="rr-callout__icon" style="background:{color};color:#fff;">!</span>
            <span style="font-weight:700;color:{color};flex-shrink:0;">{label}</span>
            <span class="rr-callout__body">{msg}</span>
        </div>
        """
    )
