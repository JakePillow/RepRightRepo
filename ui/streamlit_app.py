from __future__ import annotations
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
from ui.config.tokens import TEXT, THEME
from ui.services import run_analysis_pipeline, run_followup_coaching
from ui.state import (
    append_history,
    clear_ui_message,
    initialize_session_state,
    reset_draft_session,
    reset_group,
    request_coach_note_clear,
    set_ui_busy,
    set_ui_message,
)
from ui.runtime import coach_runtime_label, demo_banner_text, demo_mode_enabled, openai_key_present
from ui.view_models import resolve_overlay_path

def inject_global_css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {{
            --rr-page-bg: {THEME['page_bg']};
            --rr-card-bg: {THEME['card_bg']};
            --rr-card-alt-bg: {THEME['card_bg_alt']};
            --rr-text: {THEME['text']};
            --rr-text-soft: {THEME['text_soft']};
            --rr-text-muted: {THEME['text_muted']};
            --rr-border: {THEME['border']};
            --rr-accent: {THEME['accent']};
            --rr-accent-hover: {THEME['accent_hover']};
            --rr-accent-soft: {THEME['accent_soft']};
            --rr-sidebar-bg: {THEME['sidebar_bg']};
            --rr-sidebar-button: {THEME['sidebar_button']};
            --rr-sidebar-button-hover: {THEME['sidebar_button_hover']};
            --rr-sidebar-text: {THEME['sidebar_text']};
            --rr-sidebar-muted: {THEME['sidebar_muted']};
        }}

        #MainMenu,
        footer,
        [data-testid="stDecoration"], .stDeployButton {{ display:none !important; }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        [data-testid="stToolbar"] {{
            visibility: visible !important;
            opacity: 1 !important;
        }}

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
        section[data-testid="stMain"] > div {{
            background: var(--rr-page-bg) !important;
            color: var(--rr-text) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        .block-container {{
            padding-top: 28px !important;
            padding-left: 32px !important;
            padding-right: 32px !important;
            max-width: 100% !important;
        }}

        [data-testid="stSidebar"] {{
            background: var(--rr-sidebar-bg) !important;
            border-right: none !important;
            box-shadow: inset -1px 0 0 rgba(255,255,255,0.06) !important;
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
            transition: background 180ms ease, transform 180ms ease, box-shadow 180ms ease !important;
        }}

        [data-testid="collapsedControl"] > button:hover,
        [data-testid="stSidebarCollapsedControl"] > button:hover {{
            background: linear-gradient(180deg, rgba(96,165,250,0.98), rgba(37,99,235,1)) !important;
            transform: translateX(1px) !important;
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
            border-radius: 12px !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            text-align: center !important;
            padding: 10px 14px !important;
            margin: 0 0 6px 0 !important;
            width: 100% !important;
        }}

        [data-testid="stSidebar"] .stButton > button:hover {{
            background: var(--rr-sidebar-button-hover) !important;
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
            background: var(--rr-card-bg) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 12px !important;
            color: var(--rr-text) !important;
            font-size: 15px !important;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="select"] > div:focus-within,
        .stSelectbox > div > div:focus-within {{
            border-color: var(--rr-accent) !important;
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12) !important;
        }}

        .stTextInput > label, .stNumberInput > label,
        .stSelectbox > label, .stFileUploader > label,
        .stTextArea > label {{
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            color: var(--rr-text-muted) !important;
        }}

        div[data-testid="stFileUploader"] section,
        div[data-testid="stFileUploaderDropzone"] {{
            background: var(--rr-card-bg) !important;
            border: 1.5px dashed var(--rr-border) !important;
            border-radius: 14px !important;
            color: var(--rr-text-soft) !important;
        }}

        div[data-testid="stFileUploader"] small,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p {{
            color: var(--rr-text-muted) !important;
        }}

        button[kind="primary"] {{
            background: var(--rr-accent) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            box-shadow: 0 4px 16px rgba(37,99,235,0.25) !important;
        }}

        button[kind="primary"]:hover {{
            background: var(--rr-accent-hover) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--rr-card-bg) !important;
            border-color: var(--rr-border) !important;
        }}

        div[data-testid="stExpander"] {{
            background: var(--rr-card-bg) !important;
            border: 1px solid var(--rr-border) !important;
            border-radius: 16px !important;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
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
            border-radius: 14px !important;
        }}

        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {{
            color: var(--rr-text) !important;
        }}

        div[data-testid="stChatInput"] > div {{
            background: var(--rr-card-bg) !important;
            border: 1.5px solid var(--rr-border) !important;
            border-radius: 14px !important;
        }}

        div[data-testid="stChatInput"] textarea {{
            color: var(--rr-text) !important;
            background: var(--rr-card-bg) !important;
        }}

        .stDownloadButton > button {{
            background: var(--rr-card-bg) !important;
            color: var(--rr-accent) !important;
            border: 1.5px solid var(--rr-accent-soft) !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-size: 13px !important;
        }}

        .stCaptionContainer, .stCaptionContainer p {{
            color: var(--rr-text-muted) !important;
        }}

        .stSpinner > div {{
            border-top-color: var(--rr-accent) !important;
        }}

<<<<<<< Updated upstream
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: var(--rr-border); border-radius: 999px; }}
=======
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

        .rr-coach-composer-intro,
        .rr-coach-history-intro {{
            margin: 8px 0 10px;
            padding: 16px 18px;
            border-radius: 20px;
            border: 1px solid var(--rr-stage-inner-border);
            background:
                linear-gradient(180deg, rgba(255,255,255,0.36), rgba(255,255,255,0.14));
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.30);
        }}

        .rr-coach-history-intro {{
            margin-top: 18px;
        }}

        .rr-coach-composer-intro__title,
        .rr-coach-history-intro__title {{
            font-size: 17px;
            font-weight: 800;
            color: var(--rr-text);
            letter-spacing: -0.02em;
        }}

        .rr-coach-composer-intro__copy,
        .rr-coach-history-intro__copy {{
            margin-top: 4px;
            color: var(--rr-text-soft);
            font-size: 13px;
            line-height: 1.6;
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
>>>>>>> Stashed changes

        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 18px !important;
                padding-right: 18px !important;
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


def render_sidebar() -> None:
    from ui.chat_store import list_threads
    busy = bool(st.session_state.get("ui_busy"))
    with st.sidebar:
        st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:20px 0 18px;">
                <div style="width:34px;height:34px;border-radius:50%;
                            background:linear-gradient(135deg,#f97316,#ea580c);
                            display:flex;align-items:center;justify-content:center;
                            font-size:16px;">🏋</div>
                <span style="font-size:17px;font-weight:900;
                             color:#ffffff;letter-spacing:-0.02em;">RepRight</span>
            </div>""", unsafe_allow_html=True)

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
            help=TEXT["sidebar"]["new_chat_help"],
        ):
            start_new_chat(st.session_state.get("exercise_choice") or "bench")
            st.rerun()

        if st.button(
            TEXT["sidebar"]["clear_chat"],
            use_container_width=True,
            disabled=busy or (not st.session_state.get("history") and not st.session_state.get("last_response")),
            help=TEXT["sidebar"]["clear_chat_help"],
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
    canonical_exercise = str(analysis.get("exercise") or st.session_state.get("exercise_choice") or "bench")
    created_at = st.session_state.get("thread_created_at") or now_iso()
    if not st.session_state.get("thread_id"):
        st.session_state.thread_id = new_thread_id(canonical_exercise)
    st.session_state.thread_created_at = created_at
    st.session_state.thread_title = thread_title(created_at, canonical_exercise)
    st.session_state.exercise_choice = canonical_exercise


def on_analyze(exercise, use_load, upload, note) -> None:
    if st.session_state.get("ui_busy"):
        return

    should_rerun = False
    set_ui_busy(True)
    clear_ui_message()
    try:
        analysis, payload, response = run_analysis_pipeline(
            upload=upload,
            exercise=exercise,
            user_message=note,
            load_kg=use_load,
            history=st.session_state.history,
        )
        _sync_thread_identity(analysis)
        st.session_state.last_analysis = analysis
        st.session_state.last_payload = payload
        st.session_state.last_response = response
        st.session_state.restore_status = None
        request_coach_note_clear()
        if note:
            append_history("user", note, now_iso())
        append_history("assistant", response.get("response_text", ""), now_iso())
        save_thread(st.session_state.thread_id)
        should_rerun = True
    except Exception as e:
        logging.exception("Analysis pipeline failed")
        set_ui_message("error", f"{TEXT['errors']['analysis_failed']} {TEXT['errors']['details_prefix']} {e}")
        should_rerun = True
    finally:
        set_ui_busy(False)
    if should_rerun:
        st.rerun()


def on_followup(follow_up, load_kg) -> None:
    if st.session_state.get("ui_busy"):
        return

    set_ui_busy(True)
    clear_ui_message()
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
        save_thread(st.session_state.thread_id)
    except Exception as e:
        logging.exception("Follow-up coaching failed")
        set_ui_message("error", f"{TEXT['errors']['followup_failed']} {TEXT['errors']['details_prefix']} {e}")
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

    # Page header
    hcol, _ = st.columns([10, 1])
    with hcol:
        st.markdown(
            f"<h1 style='font-size:26px;font-weight:900;color:#1e293b;"
            f"letter-spacing:-0.02em;margin:0 0 22px;'>"
            f"{TEXT['main_title']}</h1>",
            unsafe_allow_html=True,
        )

    ui_message = st.session_state.get("ui_message")
    if isinstance(ui_message, dict) and ui_message.get("text"):
        render_callout(ui_message.get("kind", "info"), ui_message.get("text", ""))

    if demo_mode_enabled():
        render_callout("info", demo_banner_text())

    centre, right = st.columns([1.55, 1])

    with centre:
        # Input card — white rounded card, no stray open divs
        with st.container(border=True):
            panels.render_analysis_controls(on_analyze)

        # Empty state / overlay
        overlay_path = resolve_overlay_path(
            st.session_state.last_payload, st.session_state.last_analysis,
        )
        panels.render_overlay_panel(overlay_path)

        # Recent sessions
        panels.render_recent_sessions_in_main()

    with right:
        render_restore_status_badge(st.session_state.get('restore_status'))
        panels.render_coaching_overview_panel()

        if st.session_state.last_analysis or st.session_state.last_response:
            panels.render_quality_header()
            panels.render_summary_metrics()
            panels.render_faults_panel()
            panels.render_artifacts_panel()

        panels.render_chat_panel(on_followup)


if __name__ == "__main__":
    main()
