from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_store import load_thread, new_thread_id, now_iso, save_thread, thread_title
from ui.components import panels
from ui.components.primitives import render_callout, render_restore_status_badge
from ui.config.tokens import DARK_THEME, TEXT, THEME
from ui.services import run_analysis_pipeline, run_followup_coaching
from ui.state import (
    append_history,
    bump_chat_upload_nonce,
    clear_chat_upload_notice,
    clear_ui_message,
    initialize_session_state,
    request_followup_draft_clear,
    reset_draft_session,
    reset_group,
    set_chat_upload_notice,
    set_ui_busy,
    set_ui_message,
)
from ui.view_models import resolve_overlay_path


def _live_panels_module():
    try:
        return importlib.reload(panels)
    except Exception:
        logging.exception("Failed to reload ui.components.panels")
        return panels


def _render_right_workspace(on_analyze, on_followup) -> None:
    panels_mod = _live_panels_module()
    coach_workspace = getattr(panels_mod, "render_coach_workspace", None)
    if callable(coach_workspace):
        coach_workspace(on_analyze, on_followup)
        return

    logging.warning("render_coach_workspace missing; using compatibility fallback")
    render_overview = getattr(panels_mod, "render_coaching_overview_panel", None)
    render_chat = getattr(panels_mod, "render_chat_panel", None)

    if callable(render_overview):
        render_overview()
    if callable(render_chat):
        render_chat(on_followup)
        return

    st.error("Coach workspace could not be loaded. Please refresh the app.")


def _css_vars(theme: dict[str, str]) -> str:
    return "\n".join(
        f"            --rr-{key.replace('_', '-')}: {value};"
        for key, value in theme.items()
    )


def inject_global_css() -> None:
    light_vars = _css_vars(THEME)
    dark_vars = _css_vars(DARK_THEME)
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {{
{light_vars}
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
{dark_vars}
            }}
        }}

        #MainMenu,
        footer,
        [data-testid="stDecoration"],
        .stDeployButton {{
            display: none !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        [data-testid="stToolbar"] {{
            visibility: visible !important;
            opacity: 1 !important;
        }}

        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {{
            z-index: 1000 !important;
        }}

        [data-testid="collapsedControl"] > button,
        [data-testid="stSidebarCollapsedControl"] > button {{
            background: linear-gradient(180deg, rgba(59,130,246,0.94), rgba(29,78,216,1)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.14) !important;
            border-radius: 0 14px 14px 0 !important;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18) !important;
        }}

        [data-testid="collapsedControl"] > button:hover,
        [data-testid="stSidebarCollapsedControl"] > button:hover {{
            background: linear-gradient(180deg, rgba(96,165,250,0.98), rgba(37,99,235,1)) !important;
        }}

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        section[data-testid="stMain"],
        section[data-testid="stMain"] > div {{
            background:
                radial-gradient(circle at top left, var(--rr-stage-glow-a), transparent 36%),
                radial-gradient(circle at top right, var(--rr-stage-glow-b), transparent 32%),
                linear-gradient(180deg, var(--rr-page-bg-alt), var(--rr-page-bg)) !important;
            color: var(--rr-text) !important;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif !important;
            overflow-y: auto !important;
        }}

        .block-container {{
            position: relative !important;
            padding-top: 28px !important;
            padding-left: 32px !important;
            padding-right: 32px !important;
            max-width: 100% !important;
            background:
                linear-gradient(180deg, var(--rr-stage-bg), var(--rr-stage-bg-alt)) !important;
            border: 1px solid var(--rr-stage-border) !important;
            border-radius: 34px !important;
            box-shadow:
                0 28px 70px var(--rr-glass-shadow-strong),
                inset 0 1px 0 rgba(255,255,255,0.48) !important;
            overflow: visible !important;
            backdrop-filter: blur(22px) saturate(140%);
            margin-top: 12px !important;
            margin-bottom: 16px !important;
        }}

        .block-container::before {{
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle at 18% 8%, var(--rr-stage-glow-a), transparent 30%),
                radial-gradient(circle at 88% 2%, var(--rr-stage-glow-b), transparent 24%),
                linear-gradient(180deg, rgba(255,255,255,0.18), transparent 24%, transparent 76%, rgba(255,255,255,0.12)),
                repeating-linear-gradient(135deg, var(--rr-pattern-line) 0 2px, transparent 2px 20px);
            opacity: 0.95;
        }}

        .block-container::after {{
            content: "";
            position: absolute;
            inset: 22px;
            border-radius: 28px;
            border: 1px solid var(--rr-stage-inner-border);
            pointer-events: none;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.32);
        }}

        .block-container > * {{
            position: relative;
            z-index: 1;
        }}

        [data-testid="stSidebar"] {{
            background:
                radial-gradient(circle at top, rgba(255,255,255,0.10), transparent 32%),
                linear-gradient(180deg, var(--rr-sidebar-bg), color-mix(in srgb, var(--rr-sidebar-bg) 82%, black)) !important;
            border-right: none !important;
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.06) !important;
        }}

        [data-testid="stSidebar"] * {{
            color: var(--rr-sidebar-text) !important;
        }}

        [data-testid="stSidebar"] .stMarkdown p {{
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: var(--rr-sidebar-muted) !important;
            margin: 16px 0 6px !important;
        }}

        [data-testid="stSidebar"] .stButton > button {{
            background: var(--rr-sidebar-button) !important;
            color: var(--rr-sidebar-text) !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 16px !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            text-align: center !important;
            padding: 11px 14px !important;
            margin: 0 0 6px 0 !important;
            width: 100% !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.12) !important;
            transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease !important;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--rr-sidebar-button-hover) !important;
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.16) !important;
        }}

        [data-testid="stSidebar"] .stButton > button:disabled,
        button[kind="primary"]:disabled {{
            opacity: 0.55 !important;
            cursor: not-allowed !important;
        }}

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stSelectbox > div > div {{
            background: var(--rr-glass-bg-strong) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 16px !important;
            color: var(--rr-text) !important;
            font-size: 15px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.22) !important;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within,
        .stSelectbox > div > div:focus-within {{
            border-color: var(--rr-accent) !important;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
        }}

        .stTextInput > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stFileUploader > label,
        .stTextArea > label {{
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: var(--rr-text-muted) !important;
        }}

        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploaderDropzone"] {{
            background: var(--rr-glass-bg) !important;
            border: 1.5px dashed var(--rr-border) !important;
            border-radius: 18px !important;
            color: var(--rr-text-soft) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.20) !important;
        }}

        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p {{
            color: var(--rr-text-muted) !important;
        }}

        button[kind="primary"] {{
            background:
                linear-gradient(180deg, color-mix(in srgb, var(--rr-accent) 78%, white), var(--rr-accent)) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 16px !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            box-shadow: 0 10px 26px color-mix(in srgb, var(--rr-accent) 26%, transparent) !important;
            transition: transform 180ms ease, box-shadow 180ms ease, background 180ms ease !important;
        }}

        button[kind="primary"]:hover {{
            background: var(--rr-accent-hover) !important;
            transform: translateY(-1px);
            box-shadow: 0 14px 30px color-mix(in srgb, var(--rr-accent-hover) 30%, transparent) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--rr-glass-bg) !important;
            border: 1px solid var(--rr-glass-border) !important;
            border-radius: 24px !important;
            box-shadow:
                0 22px 48px var(--rr-glass-shadow),
                inset 0 1px 0 rgba(255,255,255,0.24) !important;
            backdrop-filter: blur(24px) saturate(150%);
            transition: transform 220ms ease, box-shadow 220ms ease, background 220ms ease !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            transform: translateY(-1px);
            box-shadow:
                0 26px 54px var(--rr-glass-shadow-strong),
                inset 0 1px 0 rgba(255,255,255,0.28) !important;
        }}

        div[data-testid="stExpander"] {{
            background: var(--rr-card-bg-alt) !important;
            border: 1px solid var(--rr-border) !important;
            border-radius: 18px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 10px 24px var(--rr-glass-shadow) !important;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p {{
            color: var(--rr-text-muted) !important;
            font-size: 12px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
        }}

        div[data-testid="stExpanderDetails"] p,
        div[data-testid="stExpanderDetails"] span {{
            color: var(--rr-text-soft) !important;
        }}

        div[data-testid="stChatMessage"] {{
            background: var(--rr-card-bg) !important;
            border: 1px solid var(--rr-border) !important;
            border-radius: 20px !important;
            box-shadow: 0 12px 24px var(--rr-glass-shadow) !important;
            backdrop-filter: blur(18px) saturate(145%);
        }}

        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {{
            color: var(--rr-text) !important;
        }}

        div[data-testid="stChatMessage"][data-testid*="ChatMessage-user"],
        div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) {{
            background: color-mix(in srgb, var(--rr-accent-soft) 72%, var(--rr-card-bg)) !important;
        }}

        div[data-testid="stChatInput"] > div {{
            background: var(--rr-glass-bg-strong) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 18px !important;
        }}

        div[data-testid="stChatInput"] textarea {{
            color: var(--rr-text) !important;
            background: var(--rr-card-bg) !important;
        }}

        .stDownloadButton > button {{
            background: var(--rr-glass-bg-strong) !important;
            color: var(--rr-accent) !important;
            border: 1.5px solid var(--rr-accent-soft) !important;
            border-radius: 16px !important;
            font-weight: 700 !important;
            font-size: 13px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.18) !important;
        }}

        .stCaptionContainer,
        .stCaptionContainer p {{
            color: var(--rr-text-muted) !important;
        }}

        .stSpinner > div {{
            border-top-color: var(--rr-accent) !important;
        }}

        .rr-section-kicker,
        .rr-kicker {{
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        .rr-section-kicker {{
            color: var(--rr-text-muted);
            margin-bottom: 6px;
        }}

        .rr-kicker--light {{
            color: rgba(255,255,255,0.74);
            margin-bottom: 8px;
        }}

        .rr-session-row,
        .rr-metric-card,
        .rr-fault-row,
        .rr-assistant-note,
        .rr-empty-card,
        .rr-callout,
        .rr-dialog-hero {{
            background: var(--rr-card-bg) !important;
            border: 1px solid var(--rr-border) !important;
            box-shadow: 0 16px 30px var(--rr-glass-shadow), inset 0 1px 0 rgba(255,255,255,0.22);
            backdrop-filter: blur(18px) saturate(150%);
        }}

        .rr-session-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 14px 18px;
            margin-bottom: 8px;
            border-radius: 16px;
            color: var(--rr-text-soft);
            font-size: 14px;
            font-weight: 700;
        }}

        .rr-session-row__arrow {{
            color: var(--rr-text-muted);
            font-size: 17px;
        }}

        .rr-metric-card {{
            text-align: center;
            border-radius: 18px;
            padding: 20px 12px;
        }}

        .rr-metric-card__label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 8px;
        }}

        .rr-metric-card__value {{
            font-size: 28px;
            font-weight: 900;
            color: var(--rr-text);
        }}

        .rr-fault-row {{
            padding: 11px 16px;
            margin-bottom: 6px;
            border-radius: 14px;
            font-size: 14px;
            color: var(--rr-text-soft);
        }}

        .rr-fault-row--comparison {{
            background: color-mix(in srgb, var(--rr-accent-soft) 34%, var(--rr-card-bg));
        }}

        .rr-glass-card,
        .rr-dialog-hero,
        .rr-hero-card {{
            position: relative;
            overflow: hidden;
        }}

        .rr-hero-card {{
            background:
                radial-gradient(circle at top left, var(--rr-hero-highlight), transparent 30%),
                linear-gradient(135deg, var(--rr-hero-from), var(--rr-hero-via) 56%, var(--rr-hero-to));
            border-radius: 24px;
            padding: 20px 20px 18px;
            color: #ffffff;
            box-shadow: 0 22px 40px color-mix(in srgb, var(--rr-accent) 20%, transparent);
            margin-bottom: 14px;
            border: 1px solid rgba(255,255,255,0.14);
        }}

        .rr-hero-card::after {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.12), transparent 32%, transparent 72%, rgba(255,255,255,0.10));
            pointer-events: none;
        }}

        .rr-hero-card__head {{
            display: flex;
            justify-content: space-between;
            gap: 14px;
            align-items: flex-start;
        }}

        .rr-hero-card__title,
        .rr-dialog-hero__title {{
            font-size: 22px;
            font-weight: 900;
            line-height: 1.1;
            letter-spacing: -0.02em;
        }}

        .rr-hero-card__copy {{
            font-size: 14px;
            color: rgba(255,255,255,0.84);
            line-height: 1.65;
            max-width: 46ch;
        }}

        .rr-hero-card__score {{
            min-width: 96px;
            text-align: right;
        }}

        .rr-hero-card__score-value {{
            font-size: 38px;
            font-weight: 900;
            line-height: 0.95;
        }}

        .rr-hero-card__score-scale {{
            font-size: 12px;
            color: rgba(255,255,255,0.78);
            margin-top: 6px;
        }}

        .rr-chip-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 16px;
        }}

        .rr-chip {{
            border-radius: 999px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.01em;
        }}

        .rr-chip--hero {{
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.14);
            color: #ffffff;
        }}

        .rr-chip--compare {{
            background: var(--rr-card-bg);
            border: 1px solid var(--rr-border);
            color: var(--rr-text-soft);
        }}

        .rr-chip--compare-good {{
            background: color-mix(in srgb, #16a34a 18%, var(--rr-card-bg));
            color: #166534;
            border-color: color-mix(in srgb, #16a34a 24%, transparent);
        }}

        .rr-chip--compare-bad {{
            background: color-mix(in srgb, #dc2626 14%, var(--rr-card-bg));
            color: #991b1b;
            border-color: color-mix(in srgb, #dc2626 24%, transparent);
        }}

        .rr-chip--compare-neutral {{
            background: color-mix(in srgb, var(--rr-accent-soft) 36%, var(--rr-card-bg));
            color: var(--rr-text-soft);
        }}

        .rr-compare-strip,
        .rr-comparison-shell,
        .rr-comparison-metric {{
            background: var(--rr-card-bg);
            border: 1px solid var(--rr-border);
            box-shadow: 0 16px 30px var(--rr-glass-shadow), inset 0 1px 0 rgba(255,255,255,0.22);
            backdrop-filter: blur(18px) saturate(150%);
        }}

        .rr-compare-strip {{
            margin: 0 0 14px;
            padding: 14px 16px 16px;
            border-radius: 18px;
        }}

        .rr-compare-strip__summary,
        .rr-comparison-summary {{
            color: var(--rr-text-soft);
            font-size: 14px;
            line-height: 1.55;
            margin-bottom: 10px;
        }}

        .rr-comparison-note {{
            color: var(--rr-text-muted);
            font-size: 12px;
            line-height: 1.5;
            margin-bottom: 10px;
        }}

        .rr-comparison-shell {{
            padding: 16px 18px;
            border-radius: 18px;
            margin: 12px 0 12px;
        }}

        .rr-comparison-metric {{
            border-radius: 18px;
            padding: 16px 14px;
            margin-bottom: 10px;
        }}

        .rr-comparison-metric__label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 8px;
        }}

        .rr-comparison-metric__delta {{
            font-size: 26px;
            font-weight: 900;
            line-height: 1;
            margin-bottom: 8px;
            color: var(--rr-text);
        }}

        .rr-comparison-metric__delta-label {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 6px;
        }}

        .rr-comparison-metric__values {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            color: var(--rr-text-soft);
            font-size: 13px;
        }}

        .rr-comparison-metric--good .rr-comparison-metric__delta {{
            color: #15803d;
        }}

        .rr-comparison-metric--bad .rr-comparison-metric__delta {{
            color: #b91c1c;
        }}

        .rr-comparison-metric--neutral .rr-comparison-metric__delta {{
            color: var(--rr-accent);
        }}

        .rr-hero-step {{
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin-top: 10px;
        }}

        .rr-hero-step__icon {{
            width: 30px;
            height: 30px;
            border-radius: 10px;
            background: rgba(255,255,255,0.14);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
        }}

        .rr-hero-step__title {{
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
        }}

        .rr-hero-step__desc {{
            font-size: 12px;
            color: rgba(255,255,255,0.78);
            line-height: 1.5;
        }}

        .rr-dialog-hero {{
            border-radius: 20px;
            padding: 18px 18px 16px;
            margin-bottom: 16px;
            background:
                linear-gradient(180deg, color-mix(in srgb, var(--rr-accent-soft) 45%, var(--rr-card-bg)), var(--rr-card-bg));
        }}

        .rr-dialog-hero__head {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
        }}

        .rr-dialog-hero__title {{
            color: var(--rr-text);
        }}

        .rr-dialog-hero__load {{
            font-size: 13px;
            font-weight: 800;
            color: var(--rr-accent);
        }}

        .rr-quality-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 28px 20px 22px;
            border-radius: 22px;
            margin-bottom: 14px;
        }}

        .rr-quality-badge__title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 16px;
        }}

        .rr-quality-badge__ring {{
            position: relative;
            width: 110px;
            height: 110px;
            margin-bottom: 14px;
        }}

        .rr-quality-badge__value-wrap {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .rr-quality-badge__value {{
            font-size: 30px;
            font-weight: 900;
            line-height: 1;
        }}

        .rr-quality-badge__scale {{
            font-size: 10px;
            color: var(--rr-text-muted);
            margin-top: 2px;
        }}

        .rr-quality-badge__zone {{
            border: 1.5px solid;
            border-radius: 999px;
            padding: 4px 18px;
            font-size: 13px;
            font-weight: 700;
        }}

        .rr-empty-card {{
            padding: 48px 24px;
            text-align: center;
            border-radius: 18px;
            color: var(--rr-text-muted);
            font-size: 14px;
            line-height: 1.7;
        }}

        .rr-empty-card--results {{
            padding: 52px 32px;
            margin: 4px 0;
        }}

        .rr-empty-card__icon {{
            font-size: 36px;
            margin-bottom: 12px;
        }}

        .rr-empty-card__icon--large {{
            font-size: 40px;
            margin-bottom: 14px;
        }}

        .rr-empty-card__title {{
            font-size: 17px;
            font-weight: 800;
            color: var(--rr-text);
            margin-bottom: 8px;
        }}

        .rr-empty-card__body {{
            font-size: 14px;
            color: var(--rr-text-muted);
            max-width: 42ch;
            margin: 0 auto;
            line-height: 1.7;
        }}

        .rr-callout {{
            background: color-mix(in srgb, var(--rr-callout-bg) 68%, var(--rr-card-bg));
            border: 1.5px solid color-mix(in srgb, var(--rr-callout-color) 32%, transparent);
            border-radius: 16px;
            padding: 12px 16px;
            margin: 8px 0;
            color: var(--rr-callout-color);
            font-size: 14px;
            font-weight: 600;
            display: flex;
            gap: 10px;
        }}

        .rr-callout__body {{
            color: var(--rr-text-soft);
        }}

        .rr-coach-shell-head {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }}

        .rr-coach-shell-head__title {{
            font-size: 21px;
            font-weight: 900;
            color: var(--rr-text);
            letter-spacing: -0.02em;
        }}

        .rr-assistant-note {{
            border-radius: 16px;
            padding: 16px 18px;
            color: var(--rr-text-soft);
            line-height: 1.7;
            white-space: pre-line;
        }}

        ::-webkit-scrollbar {{
            width: 6px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--rr-border);
            border-radius: 999px;
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 18px !important;
                padding-right: 18px !important;
                border-radius: 24px !important;
            }}

            .block-container::after {{
                inset: 14px;
                border-radius: 18px;
            }}

            .rr-hero-card__head,
            .rr-dialog-hero__head {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .rr-hero-card__score {{
                text-align: left;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    from ui.chat_store import list_threads

    busy = bool(st.session_state.get("ui_busy"))
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;padding:20px 0 18px;">
                <div style="width:34px;height:34px;border-radius:50%;
                            background:linear-gradient(135deg,#f97316,#ea580c);
                            display:flex;align-items:center;justify-content:center;
                            font-size:16px;">🏋</div>
                <span style="font-size:17px;font-weight:900;
                             color:#ffffff;letter-spacing:-0.02em;">RepRight</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            TEXT["sidebar"]["new_chat"],
            use_container_width=True,
            disabled=busy,
            help=TEXT["sidebar"].get("new_chat_help"),
        ):
            start_new_chat(st.session_state.get("exercise_choice") or "bench")
            st.rerun()

        if st.button(
            TEXT["sidebar"]["clear_chat"],
            use_container_width=True,
            disabled=busy or (
                not st.session_state.get("history")
                and not st.session_state.get("last_response")
            ),
            help=TEXT["sidebar"].get("clear_chat_help"),
        ):
            reset_group("chat")
            clear_ui_message()
            if st.session_state.thread_id:
                save_thread(st.session_state.thread_id)
            st.rerun()

        all_threads = list_threads()
        if all_threads:
            st.markdown(TEXT["sidebar"]["sessions_header"])
            for thread in all_threads[:6]:
                tid = thread.get("thread_id")
                if st.button(
                    thread.get("title") or tid,
                    key=f"top_{tid}",
                    use_container_width=True,
                    disabled=busy,
                ):
                    load_thread(tid)
                    st.rerun()

        if len(all_threads) > 6:
            st.markdown(TEXT["sidebar"]["recent_header"])
            for thread in all_threads[6:12]:
                tid = thread.get("thread_id")
                if st.button(
                    thread.get("title") or tid,
                    key=f"rec_{tid}",
                    use_container_width=True,
                    disabled=busy,
                ):
                    load_thread(tid)
                    st.rerun()


def start_new_chat(exercise: str) -> None:
    reset_draft_session(exercise)


def _sync_thread_identity(analysis: dict) -> None:
    canonical_exercise = str(
        analysis.get("exercise")
        or st.session_state.get("exercise_choice")
        or "bench"
    )
    created_at = st.session_state.get("thread_created_at") or now_iso()
    if not st.session_state.get("thread_id"):
        st.session_state.thread_id = new_thread_id(canonical_exercise)
    st.session_state.thread_created_at = created_at
    st.session_state.thread_title = thread_title(created_at, canonical_exercise)
    st.session_state.exercise_choice = canonical_exercise


def _analysis_history_message(exercise: str, load_kg: float | None, note: str, comparison_mode: bool) -> str:
    exercise_label = str(exercise or "set").capitalize()
    load_label = f"{float(load_kg):.1f} kg" if isinstance(load_kg, (int, float)) else "load n/a"
    prefix = "Uploaded follow-up set for comparison" if comparison_mode else "Uploaded set for analysis"
    if note:
        return f"{prefix}: {exercise_label} ({load_label}). Note: {note}"
    return f"{prefix}: {exercise_label} ({load_label})."


def on_analyze(exercise, use_load, upload, note) -> None:
    if st.session_state.get("ui_busy"):
        return

    should_rerun = False
    previous_analysis = st.session_state.get("last_analysis") if st.session_state.get("last_analysis") else None
    previous_load_kg = st.session_state.get("last_analysis_load_kg")
    comparison_mode = bool(previous_analysis)
    set_ui_busy(True)
    clear_ui_message()
    clear_chat_upload_notice()
    try:
        analysis, payload, response = run_analysis_pipeline(
            upload=upload,
            exercise=exercise,
            user_message=note,
            load_kg=use_load,
            history=st.session_state.history,
            previous_analysis=previous_analysis,
            previous_load_kg=previous_load_kg,
        )
        _sync_thread_identity(analysis)
        st.session_state.last_analysis = analysis
        st.session_state.last_analysis_load_kg = use_load
        st.session_state.last_payload = payload
        st.session_state.last_response = response
        st.session_state.restore_status = None
        request_followup_draft_clear()
        append_history(
            "user",
            _analysis_history_message(exercise, use_load, note, comparison_mode),
            now_iso(),
        )
        append_history("assistant", response.get("response_text", ""), now_iso())
        save_thread(st.session_state.thread_id)
        should_rerun = True
    except Exception as exc:
        logging.exception("Analysis pipeline failed")
        set_chat_upload_notice(
            "error",
            (
                "This upload could not be analyzed, so your current chat and last valid analysis were kept intact. "
                f"{TEXT['errors']['details_prefix']} {exc}"
            ),
        )
        if not comparison_mode:
            set_ui_message(
                "error",
                f"{TEXT['errors']['analysis_failed']} {TEXT['errors']['details_prefix']} {exc}",
            )
        should_rerun = True
    finally:
        bump_chat_upload_nonce()
        set_ui_busy(False)

    if should_rerun:
        st.rerun()


def on_followup(follow_up, load_kg) -> None:
    if st.session_state.get("ui_busy"):
        return

    set_ui_busy(True)
    clear_ui_message()
    clear_chat_upload_notice()
    try:
        payload, response = run_followup_coaching(
            analysis=st.session_state.last_analysis,
            follow_up=follow_up,
            load_kg=load_kg,
            history=st.session_state.history,
        )
        st.session_state.last_payload = payload
        st.session_state.last_response = response
        append_history("user", follow_up, now_iso())
        append_history("assistant", response.get("response_text", ""), now_iso())
        request_followup_draft_clear()
        if st.session_state.thread_id:
            save_thread(st.session_state.thread_id)
    except Exception as exc:
        logging.exception("Follow-up coaching failed")
        set_ui_message(
            "error",
            f"{TEXT['errors']['followup_failed']} {TEXT['errors']['details_prefix']} {exc}",
        )
    finally:
        set_ui_busy(False)

    st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="RepRight",
        page_icon="🏋️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    initialize_session_state()
    inject_global_css()
    render_sidebar()

    hcol, _ = st.columns([10, 1])
    with hcol:
        st.markdown(
            (
                "<h1 style='font-size:26px;font-weight:900;color:#1e293b;"
                "letter-spacing:-0.02em;margin:0 0 22px;'>"
                f"{TEXT['main_title']}</h1>"
            ),
            unsafe_allow_html=True,
        )

    ui_message = st.session_state.get("ui_message")
    if isinstance(ui_message, dict) and ui_message.get("text"):
        render_callout(ui_message.get("kind", "info"), ui_message.get("text", ""))

    centre, right = st.columns([1.55, 1])

    with centre:
        with st.container(border=True):
            overlay_path = resolve_overlay_path(
                st.session_state.last_payload,
                st.session_state.last_analysis,
            )
            panels.render_overlay_panel(overlay_path)
            panels.render_recent_sessions_in_main()

    with right:
        render_restore_status_badge(st.session_state.get("restore_status"))
        _render_right_workspace(on_analyze, on_followup)


if __name__ == "__main__":
    main()
