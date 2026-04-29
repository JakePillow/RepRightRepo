from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.chat_store import list_threads, load_thread, new_thread_id, now_iso, save_thread, thread_title
import ui.components.panels as panels
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
try:
    from .runtime import coach_runtime_label, demo_banner_text, demo_mode_enabled, openai_key_present
except Exception:
    from ui.runtime import coach_runtime_label, demo_banner_text, demo_mode_enabled, openai_key_present
from ui.theme_css import build_global_css
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
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&display=swap');

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

        /* Wii sidebar toggle button — blue bubble */
        [data-testid="collapsedControl"] > button,
        [data-testid="stSidebarCollapsedControl"] > button {{
            background: linear-gradient(180deg, #0066CC, #003F8A) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255,255,255,0.18) !important;
            border-radius: 0 20px 20px 0 !important;
            box-shadow: 0 8px 20px rgba(0, 30, 80, 0.28), inset 0 1px 0 rgba(255,255,255,0.28) !important;
        }}

        [data-testid="collapsedControl"] > button:hover,
        [data-testid="stSidebarCollapsedControl"] > button:hover {{
            background: linear-gradient(180deg, #4DB3FF, #0057B7) !important;
        }}

        /* === Final dark dashboard background === */
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        section[data-testid="stMain"],
        section[data-testid="stMain"] > div {{
            background:
                radial-gradient(circle at 12% 0%, rgba(59,130,246,0.25), transparent 34%),
                radial-gradient(circle at 92% 0%, rgba(14,165,233,0.18), transparent 30%),
                linear-gradient(180deg, #020817 0%, #06122d 55%, #030c20 100%) !important;
            color: var(--rr-text) !important;
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
            overflow-y: auto !important;
        }}

        /* === Dashboard shell === */
        .block-container {{
            position: relative !important;
            padding-top: 28px !important;
            padding-left: 30px !important;
            padding-right: 30px !important;
            max-width: 1320px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            background: linear-gradient(180deg, rgba(5,15,35,0.96), rgba(3,11,28,0.98)) !important;
            border: 1px solid rgba(96,165,250,0.24) !important;
            border-radius: 22px !important;
            box-shadow:
                0 24px 64px rgba(2,6,23,0.72),
                inset 0 1px 0 rgba(255,255,255,0.10) !important;
            overflow: visible !important;
            backdrop-filter: blur(14px) saturate(116%);
            margin-top: 12px !important;
            margin-bottom: 20px !important;
        }}

        /* Subtle glow overlay */
        .block-container::before {{
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 22px;
            pointer-events: none;
            background:
                radial-gradient(circle at 18% 8%, rgba(59,130,246,0.20), transparent 30%),
                radial-gradient(circle at 88% 2%, rgba(14,165,233,0.14), transparent 26%),
                linear-gradient(180deg, rgba(255,255,255,0.08) 0%, transparent 22%, transparent 82%, rgba(255,255,255,0.03) 100%);
            z-index: 0;
        }}

        .block-container::after {{
            content: "";
            position: absolute;
            inset: 16px;
            border-radius: 16px;
            border: 1px solid rgba(96,165,250,0.18);
            pointer-events: none;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
            z-index: 0;
        }}

        .block-container > * {{
            position: relative;
            z-index: 1;
        }}

        /* === Wii Settings sidebar: deep navy === */
        [data-testid="stSidebar"] {{
            background:
                radial-gradient(ellipse at top, rgba(0,102,204,0.22), transparent 42%),
                linear-gradient(180deg, var(--rr-sidebar-bg) 0%, #000D2A 100%) !important;
            border-right: none !important;
            box-shadow: inset -1px 0 0 rgba(77,179,255,0.12) !important;
        }}

        [data-testid="stSidebar"] * {{
            color: var(--rr-sidebar-text) !important;
        }}

        [data-testid="stSidebar"] .stMarkdown p {{
            font-size: 11px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.10em !important;
            color: var(--rr-sidebar-muted) !important;
            margin: 16px 0 6px !important;
        }}

        /* Wii menu sidebar buttons — translucent white bubbles on navy */
        [data-testid="stSidebar"] .stButton > button {{
            background: var(--rr-sidebar-button) !important;
            color: var(--rr-sidebar-text) !important;
            border: 1px solid rgba(255,255,255,0.12) !important;
            border-radius: 22px !important;
            font-size: 13px !important;
            font-weight: 800 !important;
            font-family: "Nunito", sans-serif !important;
            text-align: center !important;
            padding: 11px 14px !important;
            margin: 0 0 6px 0 !important;
            width: 100% !important;
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.18),
                0 2px 8px rgba(0,0,0,0.18) !important;
            transition: transform 160ms ease, background 160ms ease, box-shadow 160ms ease !important;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--rr-sidebar-button-hover) !important;
            transform: translateY(-1px) scale(1.01);
            box-shadow: 0 8px 20px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.22) !important;
        }}

        [data-testid="stSidebar"] .stButton > button:disabled,
        button[kind="primary"]:disabled {{
            opacity: 0.50 !important;
            cursor: not-allowed !important;
        }}

        /* === Dashboard input controls === */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stSelectbox > div > div {{
            background: rgba(30, 41, 59, 0.72) !important;
            border: 1px solid rgba(96,165,250,0.24) !important;
            border-radius: 10px !important;
            color: #e2e8f0 !important;
            font-size: 15px !important;
            font-family: "Inter", sans-serif !important;
            font-weight: 500 !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08) !important;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within,
        .stSelectbox > div > div:focus-within {{
            border-color: var(--rr-accent) !important;
            box-shadow: 0 0 0 3px rgba(59,130,246,0.22), inset 0 1px 0 rgba(255,255,255,0.10) !important;
        }}

        .stTextInput > label,
        .stNumberInput > label,
        .stSelectbox > label,
        .stFileUploader > label,
        .stTextArea > label {{
            font-size: 11px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.10em !important;
            color: var(--rr-text-muted) !important;
            font-family: "Nunito", sans-serif !important;
        }}

        /* === Wii file uploader: white with dashed blue border === */
        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploaderDropzone"] {{
            background: var(--rr-glass-bg-strong) !important;
            border: 2px dashed var(--rr-accent) !important;
            border-radius: 22px !important;
            color: var(--rr-text-soft) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.60), 0 4px 16px rgba(0,87,183,0.08) !important;
        }}

        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p {{
            color: var(--rr-text-muted) !important;
        }}

        /* === Dashboard primary button === */
        button[kind="primary"] {{
            background:
                linear-gradient(180deg, #3b82f6 0%, #2563eb 100%) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(96,165,250,0.32) !important;
            border-radius: 10px !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            font-family: "Inter", sans-serif !important;
            letter-spacing: 0.01em !important;
            box-shadow:
                0 8px 22px rgba(37,99,235,0.35),
                inset 0 1px 0 rgba(255,255,255,0.20) !important;
            transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease !important;
        }}

        button[kind="primary"]:hover {{
            background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%) !important;
            transform: translateY(-2px) scale(1.01);
            box-shadow:
                0 14px 30px rgba(37,99,235,0.44),
                inset 0 1px 0 rgba(255,255,255,0.22) !important;
        }}

        /* === Wii channel card: white frosted, blue border, gloss === */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--rr-glass-bg-strong) !important;
            border: 1.5px solid var(--rr-glass-border) !important;
            border-radius: 26px !important;
            box-shadow:
                0 18px 44px var(--rr-glass-shadow),
                inset 0 2px 0 rgba(255,255,255,0.70),
                inset 0 -1px 0 rgba(0,87,183,0.06) !important;
            backdrop-filter: blur(20px) saturate(140%);
            transition: transform 200ms ease, box-shadow 200ms ease !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            transform: translateY(-2px);
            box-shadow:
                0 24px 52px var(--rr-glass-shadow-strong),
                inset 0 2px 0 rgba(255,255,255,0.74) !important;
        }}

        div[data-testid="stExpander"] {{
            background: var(--rr-card-bg-alt) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 20px !important;
            box-shadow: inset 0 2px 0 rgba(255,255,255,0.60), 0 8px 20px var(--rr-glass-shadow) !important;
        }}

        div[data-testid="stExpander"] summary,
        div[data-testid="stExpander"] summary p {{
            color: var(--rr-text-muted) !important;
            font-size: 12px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.10em !important;
            font-family: "Nunito", sans-serif !important;
        }}

        div[data-testid="stExpanderDetails"] p,
        div[data-testid="stExpanderDetails"] span {{
            color: var(--rr-text-soft) !important;
        }}

        /* === Wii chat bubble style === */
        div[data-testid="stChatMessage"] {{
            background: var(--rr-glass-bg-strong) !important;
            border: 1.5px solid var(--rr-glass-border) !important;
            border-radius: 22px !important;
            box-shadow:
                0 10px 24px var(--rr-glass-shadow),
                inset 0 1px 0 rgba(255,255,255,0.60) !important;
            backdrop-filter: blur(16px) saturate(140%);
        }}

        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {{
            color: var(--rr-text) !important;
        }}

        div[data-testid="stChatMessage"][data-testid*="ChatMessage-user"],
        div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) {{
            background: rgba(0,102,204,0.08) !important;
            border-color: rgba(0,87,183,0.18) !important;
        }}

        div[data-testid="stChatInput"] > div {{
            background: var(--rr-glass-bg-strong) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 22px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.60) !important;
        }}

        div[data-testid="stChatInput"] textarea {{
            color: var(--rr-text) !important;
            background: transparent !important;
            font-family: "Nunito", sans-serif !important;
        }}

        .stDownloadButton > button {{
            background: var(--rr-glass-bg-strong) !important;
            color: var(--rr-accent) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 20px !important;
            font-weight: 800 !important;
            font-size: 13px !important;
            font-family: "Nunito", sans-serif !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.60) !important;
        }}

        .stCaptionContainer,
        .stCaptionContainer p {{
            color: var(--rr-text-muted) !important;
            font-family: "Nunito", sans-serif !important;
        }}

        .stSpinner > div {{
            border-top-color: var(--rr-accent) !important;
        }}

        /* === Wii typography: Nunito rounded headings === */
        .rr-page-title {{
            text-align: center;
            font-size: 48px;
            font-weight: 900;
            letter-spacing: -0.03em;
            margin: 2px 0 28px;
            color: #f8fafc;
            text-shadow: 0 0 24px rgba(59,130,246,0.22);
        }}

        .rr-section-kicker,
        .rr-kicker {{
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-family: "Inter", sans-serif;
        }}

        .rr-section-kicker {{
            color: var(--rr-text-muted);
            margin-bottom: 6px;
        }}

        .rr-kicker--light {{
            color: rgba(255,255,255,0.80);
            margin-bottom: 8px;
        }}

        /* === Wii-style card components === */
        .rr-session-row,
        .rr-metric-card,
        .rr-fault-row,
        .rr-assistant-note,
        .rr-empty-card,
        .rr-callout,
        .rr-dialog-hero {{
            background: linear-gradient(180deg, rgba(15,23,42,0.78), rgba(9,16,30,0.90)) !important;
            border: 1px solid rgba(96,165,250,0.24) !important;
            box-shadow: 0 10px 26px rgba(2,6,23,0.46), inset 0 1px 0 rgba(255,255,255,0.10);
            backdrop-filter: blur(16px) saturate(140%);
        }}

        .rr-session-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 14px 18px;
            margin-bottom: 8px;
            border-radius: 20px;
            color: var(--rr-text-soft);
            font-size: 14px;
            font-weight: 700;
            font-family: "Nunito", sans-serif;
        }}

        .rr-session-row__arrow {{
            color: var(--rr-accent);
            font-size: 17px;
        }}

        .rr-metric-card {{
            text-align: center;
            border-radius: 22px;
            padding: 22px 12px;
        }}

        .rr-metric-card__label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 8px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-metric-card__value {{
            font-size: 28px;
            font-weight: 900;
            color: var(--rr-text);
            font-family: "Nunito", sans-serif;
        }}

        .rr-fault-row {{
            padding: 11px 16px;
            margin-bottom: 6px;
            border-radius: 18px;
            font-size: 14px;
            color: var(--rr-text-soft);
            font-family: "Nunito", sans-serif;
        }}

        .rr-fault-row--comparison {{
            background: rgba(0,102,204,0.07) !important;
            border-color: rgba(0,87,183,0.16) !important;
        }}

        .rr-glass-card,
        .rr-dialog-hero,
        .rr-hero-card {{
            position: relative;
            overflow: hidden;
        }}

        /* === Wii hero card: blue channel bubble with gloss shimmer === */
        .rr-hero-card {{
            background:
                linear-gradient(135deg, var(--rr-hero-from), var(--rr-hero-via) 54%, var(--rr-hero-to));
            border-radius: 26px;
            padding: 22px 22px 18px;
            color: #ffffff;
            box-shadow:
                0 20px 44px rgba(0,63,138,0.30),
                inset 0 1px 0 rgba(255,255,255,0.40);
            margin-bottom: 14px;
            border: 1.5px solid rgba(255,255,255,0.18);
        }}

        /* Wii gloss shimmer on hero card */
        .rr-hero-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 50%;
            border-radius: 26px 26px 60% 60% / 26px 26px 30px 30px;
            background: linear-gradient(180deg, rgba(255,255,255,0.28) 0%, transparent 100%);
            pointer-events: none;
        }}

        .rr-hero-card::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(180deg, transparent 60%, rgba(0,0,0,0.08) 100%);
            pointer-events: none;
            border-radius: 26px;
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
            letter-spacing: -0.01em;
            font-family: "Nunito", sans-serif;
        }}

        .rr-hero-card__copy {{
            font-size: 14px;
            color: rgba(255,255,255,0.88);
            line-height: 1.65;
            max-width: 46ch;
            font-family: "Nunito", sans-serif;
        }}

        .rr-hero-card__score {{
            min-width: 96px;
            text-align: right;
        }}

        .rr-hero-card__score-value {{
            font-size: 38px;
            font-weight: 900;
            line-height: 0.95;
            font-family: "Nunito", sans-serif;
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
            padding: 6px 14px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.01em;
            font-family: "Nunito", sans-serif;
        }}

        .rr-chip--hero {{
            background: rgba(255,255,255,0.16);
            border: 1px solid rgba(255,255,255,0.22);
            color: #ffffff;
        }}

        .rr-chip--compare {{
            background: var(--rr-glass-bg-strong);
            border: 1.5px solid var(--rr-border);
            color: var(--rr-text-soft);
        }}

        .rr-chip--compare-good {{
            background: rgba(58,140,58,0.10);
            color: #2A6B2A;
            border-color: rgba(58,140,58,0.22);
        }}

        .rr-chip--compare-bad {{
            background: rgba(192,57,43,0.10);
            color: #8B1A10;
            border-color: rgba(192,57,43,0.22);
        }}

        .rr-chip--compare-neutral {{
            background: rgba(0,102,204,0.08);
            color: var(--rr-text-soft);
            border-color: rgba(0,87,183,0.18);
        }}

        /* === Wii comparison cards === */
        .rr-compare-strip,
        .rr-comparison-shell,
        .rr-comparison-metric {{
            background: var(--rr-glass-bg-strong);
            border: 1.5px solid var(--rr-glass-border);
            box-shadow: 0 12px 28px var(--rr-glass-shadow), inset 0 1px 0 rgba(255,255,255,0.60);
            backdrop-filter: blur(16px) saturate(140%);
        }}

        .rr-compare-strip {{
            margin: 0 0 14px;
            padding: 14px 16px 16px;
            border-radius: 22px;
        }}

        .rr-compare-strip__summary,
        .rr-comparison-summary {{
            color: var(--rr-text-soft);
            font-size: 14px;
            line-height: 1.55;
            margin-bottom: 10px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-note {{
            color: var(--rr-text-muted);
            font-size: 12px;
            line-height: 1.5;
            margin-bottom: 10px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-shell {{
            padding: 16px 18px;
            border-radius: 22px;
            margin: 12px 0 12px;
        }}

        .rr-comparison-metric {{
            border-radius: 22px;
            padding: 16px 14px;
            margin-bottom: 10px;
        }}

        .rr-comparison-metric__label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 8px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-metric__delta {{
            font-size: 26px;
            font-weight: 900;
            line-height: 1;
            margin-bottom: 8px;
            color: var(--rr-text);
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-metric__delta-label {{
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.10em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 6px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-metric__values {{
            display: flex;
            flex-direction: column;
            gap: 2px;
            color: var(--rr-text-soft);
            font-size: 13px;
            font-family: "Nunito", sans-serif;
        }}

        .rr-comparison-metric--good .rr-comparison-metric__delta {{
            color: #2A7A2A;
        }}

        .rr-comparison-metric--bad .rr-comparison-metric__delta {{
            color: #C0392B;
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

        /* Wii icon button bubble */
        .rr-hero-step__icon {{
            width: 32px;
            height: 32px;
            border-radius: 12px;
            background: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.22);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 15px;
            flex-shrink: 0;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.28);
        }}

        .rr-hero-step__title {{
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
            font-family: "Nunito", sans-serif;
        }}

        .rr-hero-step__desc {{
            font-size: 12px;
            color: rgba(255,255,255,0.82);
            line-height: 1.5;
            font-family: "Nunito", sans-serif;
        }}

        .rr-dialog-hero {{
            border-radius: 22px;
            padding: 18px 18px 16px;
            margin-bottom: 16px;
            background:
                linear-gradient(180deg, rgba(0,102,204,0.10) 0%, var(--rr-glass-bg-strong) 100%) !important;
            border-color: var(--rr-glass-border) !important;
        }}

        .rr-dialog-hero__head {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
        }}

        .rr-dialog-hero__title {{
            color: var(--rr-text);
            font-family: "Nunito", sans-serif;
        }}

        .rr-dialog-hero__load {{
            font-size: 13px;
            font-weight: 800;
            color: var(--rr-accent);
            font-family: "Nunito", sans-serif;
        }}

        .rr-quality-badge {{
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            padding: 28px 20px 22px;
            border-radius: 24px;
            margin-bottom: 14px;
        }}

        .rr-quality-badge__title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--rr-text-muted);
            font-weight: 800;
            margin-bottom: 16px;
            font-family: "Nunito", sans-serif;
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
            font-family: "Nunito", sans-serif;
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
            font-family: "Nunito", sans-serif;
        }}

        .rr-empty-card {{
            padding: 48px 24px;
            text-align: center;
            border-radius: 22px;
            color: var(--rr-text-muted);
            font-size: 14px;
            line-height: 1.7;
            font-family: "Nunito", sans-serif;
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
            font-family: "Nunito", sans-serif;
        }}

        .rr-empty-card__body {{
            font-size: 14px;
            color: var(--rr-text-muted);
            max-width: 42ch;
            margin: 0 auto;
            line-height: 1.7;
            font-family: "Nunito", sans-serif;
        }}

        .rr-callout {{
            background: rgba(var(--rr-callout-bg), 0.68) !important;
            border: 1.5px solid color-mix(in srgb, var(--rr-callout-color) 28%, transparent);
            border-radius: 20px;
            padding: 12px 16px;
            margin: 8px 0;
            color: var(--rr-callout-color);
            font-size: 14px;
            font-weight: 700;
            display: flex;
            gap: 10px;
            font-family: "Nunito", sans-serif;
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
            letter-spacing: -0.01em;
            font-family: "Nunito", sans-serif;
        }}

        .rr-coach-composer-intro,
        .rr-coach-history-intro {{
            margin: 8px 0 10px;
            padding: 16px 18px;
            border-radius: 22px;
            border: 1.5px solid var(--rr-stage-inner-border);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.70) 0%, rgba(238,244,255,0.50) 100%);
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.70), 0 4px 12px rgba(0,87,183,0.06);
        }}

        .rr-coach-history-intro {{
            margin-top: 18px;
        }}

        .rr-coach-composer-intro__title,
        .rr-coach-history-intro__title {{
            font-size: 17px;
            font-weight: 800;
            color: var(--rr-text);
            letter-spacing: -0.01em;
            font-family: "Nunito", sans-serif;
        }}

        .rr-coach-composer-intro__copy,
        .rr-coach-history-intro__copy {{
            margin-top: 4px;
            color: var(--rr-text-soft);
            font-size: 13px;
            line-height: 1.6;
            font-family: "Nunito", sans-serif;
        }}

        .rr-assistant-note {{
            border-radius: 20px;
            padding: 16px 18px;
            color: var(--rr-text-soft);
            line-height: 1.7;
            white-space: pre-line;
            font-family: "Nunito", sans-serif;
        }}

        /* === Wii scrollbar: blue, rounded === */
        ::-webkit-scrollbar {{
            width: 7px;
        }}

        ::-webkit-scrollbar-track {{
            background: rgba(0,87,183,0.04);
            border-radius: 999px;
        }}

        ::-webkit-scrollbar-thumb {{
            background: rgba(0,87,183,0.22);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.50);
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(0,102,204,0.40);
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 18px !important;
                padding-right: 18px !important;
                border-radius: 26px !important;
            }}

            .block-container::after {{
                inset: 14px;
                border-radius: 20px;
            }}

            .rr-hero-card__head,
            .rr-dialog-hero__head {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .rr-hero-card__score {{
                text-align: left;
            }}

            .rr-coach-composer-intro,
            .rr-coach-history-intro {{
                padding: 14px 15px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_global_css_modern() -> None:
    light_vars = _css_vars(THEME)
    dark_vars = _css_vars(DARK_THEME)
    st.markdown(build_global_css(light_vars, dark_vars), unsafe_allow_html=True)


def render_page_hero() -> None:
    analysis = st.session_state.get("last_analysis") or {}
    exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "first set").capitalize()
    has_analysis = bool(analysis)
    session_count = len(list_threads())
    status_value = f"Reviewing {exercise}" if has_analysis else "Ready for first upload"
    status_copy = (
        "Review the replay, ask for one clear coaching change, and keep the next set moving forward."
        if has_analysis
        else "Upload one side-view set to unlock replay, movement metrics, and a coaching thread."
    )
    session_label = f"{session_count} saved session{'s' if session_count != 1 else ''}"
    mood_label = "Replay-first"
    secondary_tag = "Coach thread" if has_analysis else "Set review"

    st.markdown(
        f"""
        <section class="rr-app-header">
            <div class="rr-app-header__main">
                <div class="rr-section-kicker">Performance Review Workspace</div>
                <div class="rr-app-header__title">{TEXT['main_title']}</div>
                <div class="rr-app-header__copy">{status_copy}</div>
                <div class="rr-app-header__tags">
                    <span class="rr-app-header__tag">{mood_label}</span>
                    <span class="rr-app-header__tag">{secondary_tag}</span>
                </div>
            </div>
            <div class="rr-app-header__meta">
                <div class="rr-app-header__status-group">
                    <div class="rr-app-header__status">{status_value}</div>
                    <div class="rr-app-header__submeta">{session_label}</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_surface_head(kicker: str, title: str, copy: str, *, variant: str = "section") -> None:
    st.markdown(
        f"""
        <div class="rr-pane-head rr-pane-head--{variant}">
            <div class="rr-pane-head__eyebrow">{kicker}</div>
            <div class="rr-pane-head__title">{title}</div>
            <div class="rr-pane-head__copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    busy = bool(st.session_state.get("ui_busy"))
    with st.sidebar:
        st.markdown(
            """
            <div class="rr-sidebar-brand">
                <div class="rr-sidebar-brand__mark">RR</div>
                <div>
                    <div class="rr-sidebar-brand__name">RepRight</div>
                    <div class="rr-sidebar-brand__copy">Video form review and coaching in one workspace.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if demo_mode_enabled():
            render_callout("info", demo_banner_text())
            st.caption(
                f"Coach mode: {coach_runtime_label()} | OpenAI key: {'present' if openai_key_present() else 'missing'}"
            )
            st.caption("Demo tip: keep backup clips short, stable, and already tested on this app.")

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


def render_nav_rail() -> None:
    busy = bool(st.session_state.get("ui_busy"))
    all_threads = list_threads()

    st.markdown('<div class="rr-nav-shell"></div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="rr-sidebar-brand rr-sidebar-brand--rail">
            <div class="rr-sidebar-brand__mark">RR</div>
            <div>
                <div class="rr-sidebar-brand__name">RepRight</div>
                <div class="rr-sidebar-brand__copy">Exercise form review and coaching.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        TEXT["sidebar"]["new_chat"],
        use_container_width=True,
        disabled=busy,
        type="primary",
        key="rail_new_chat",
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
        key="rail_clear_chat",
        help=TEXT["sidebar"].get("clear_chat_help"),
    ):
        reset_group("chat")
        clear_ui_message()
        if st.session_state.thread_id:
            save_thread(st.session_state.thread_id)
        st.rerun()

    st.markdown(
        f"""
        <div class="rr-nav-meta">
            <div class="rr-nav-meta__pill">{len(all_threads)} saved session{'s' if len(all_threads) != 1 else ''}</div>
            <div class="rr-nav-meta__pill">{'Busy' if busy else 'Ready'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if demo_mode_enabled():
        render_callout("info", demo_banner_text())

    if all_threads:
        st.markdown('<div class="rr-nav-label">Sessions</div>', unsafe_allow_html=True)
        for thread in all_threads[:8]:
            tid = thread.get("thread_id")
            if st.button(
                thread.get("title") or tid,
                key=f"rail_thread_{tid}",
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
    previous_analysis = st.session_state.get("last_analysis") or None
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
                "This upload could not be analysed, so your current chat and last valid analysis were kept intact. "
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
        initial_sidebar_state="collapsed",
    )
    initialize_session_state()
    inject_global_css_modern()
    nav, workspace = st.columns([0.42, 2.58], gap="medium")

    with nav:
        render_nav_rail()

    with workspace:
        render_page_hero()

        ui_message = st.session_state.get("ui_message")
        if isinstance(ui_message, dict) and ui_message.get("text"):
            render_callout(ui_message.get("kind", "info"), ui_message.get("text", ""))

        if demo_mode_enabled():
            render_callout("info", demo_banner_text())

        has_analysis = bool(st.session_state.get("last_analysis"))
        centre, right = st.columns([3.35, 0.85], gap="large")

        with centre:
            with st.container():
                st.markdown('<div class="rr-stage-shell"></div>', unsafe_allow_html=True)
                render_surface_head(
                    "Replay",
                    "Movement Replay",
                    (
                        "Replay the set, inspect the overlay, and compare what changed before you move on."
                        if has_analysis
                        else "Your analysed replay and overlay appear here as soon as the first upload finishes."
                    ),
                    variant="stage",
                )
                overlay_path = resolve_overlay_path(
                    st.session_state.last_payload,
                    st.session_state.last_analysis,
                )
                panels.render_overlay_panel(overlay_path)

        with right:
            render_restore_status_badge(st.session_state.get("restore_status"))
            _render_right_workspace(on_analyze, on_followup)


if __name__ == "__main__":
    main()
