from __future__ import annotations


def build_global_css(light_vars: str, dark_vars: str) -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');

    :root {{
        color-scheme: light dark;
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
        position: fixed !important;
        top: max(74px, env(safe-area-inset-top)) !important;
        left: 0 !important;
        z-index: 2147483647 !important;
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        width: auto !important;
        overflow: visible !important;
    }}

    [data-testid="collapsedControl"] > button,
    [data-testid="stSidebarCollapsedControl"] > button {{
        background: var(--rr-sidebar-bg) !important;
        color: var(--rr-sidebar-text) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 0 16px 16px 0 !important;
        box-shadow: 0 12px 30px rgba(2,6,23,0.28) !important;
        min-width: 46px !important;
        min-height: 46px !important;
        padding: 0 12px !important;
        touch-action: manipulation !important;
    }}

    [data-testid="collapsedControl"] > button:hover,
    [data-testid="stSidebarCollapsedControl"] > button:hover {{
        background: #16233a !important;
    }}

    @media (max-width: 900px) {{
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {{
            top: max(66px, env(safe-area-inset-top)) !important;
        }}
    }}

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    section[data-testid="stMain"],
    section[data-testid="stMain"] > div {{
        background:
            radial-gradient(circle at top left, var(--rr-stage-glow-a), transparent 28%),
            radial-gradient(circle at top right, var(--rr-stage-glow-b), transparent 24%),
            linear-gradient(180deg, var(--rr-page-bg-alt), var(--rr-page-bg)) !important;
        color: var(--rr-text) !important;
        font-family: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
        overflow-y: auto !important;
    }}

    .block-container {{
        max-width: 1380px !important;
        padding-top: 34px !important;
        padding-bottom: 28px !important;
        padding-left: 28px !important;
        padding-right: 28px !important;
    }}

    [data-testid="stSidebar"] {{
        background:
            radial-gradient(circle at top, rgba(96,165,250,0.16), transparent 30%),
            linear-gradient(180deg, var(--rr-sidebar-bg), #111827) !important;
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
        letter-spacing: 0.14em !important;
        color: var(--rr-sidebar-muted) !important;
        margin: 16px 0 6px !important;
    }}

    .rr-sidebar-brand {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 4px 0 18px;
    }}

    .rr-sidebar-brand__mark {{
        width: 42px;
        height: 42px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #2563eb, #0f172a);
        color: #ffffff;
        font-family: "Manrope", sans-serif;
        font-size: 15px;
        font-weight: 800;
        letter-spacing: 0.06em;
        box-shadow: 0 12px 24px rgba(15, 23, 42, 0.28);
    }}

    .rr-sidebar-brand__name {{
        font-family: "Manrope", sans-serif;
        font-size: 17px;
        font-weight: 800;
        line-height: 1.1;
        color: var(--rr-sidebar-text);
    }}

    .rr-sidebar-brand__copy {{
        font-size: 12px;
        line-height: 1.5;
        color: var(--rr-sidebar-muted);
        margin-top: 4px;
    }}

    [data-testid="stSidebar"] .stButton > button {{
        background: var(--rr-sidebar-button) !important;
        color: var(--rr-sidebar-text) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 16px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        font-family: "Manrope", sans-serif !important;
        text-align: center !important;
        padding: 11px 14px !important;
        margin: 0 0 6px 0 !important;
        width: 100% !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.08) !important;
        transition: transform 180ms ease, background 180ms ease, box-shadow 180ms ease !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: var(--rr-sidebar-button-hover) !important;
        transform: translateY(-1px);
        box-shadow: 0 12px 24px rgba(2,6,23,0.20) !important;
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
        border: 1px solid var(--rr-border) !important;
        border-radius: 16px !important;
        color: var(--rr-text) !important;
        font-size: 15px !important;
        font-family: "IBM Plex Sans", sans-serif !important;
        font-weight: 500 !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.18) !important;
    }}

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="select"] > div:focus-within,
    .stSelectbox > div > div:focus-within {{
        border-color: var(--rr-accent) !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.14), inset 0 1px 0 rgba(255,255,255,0.22) !important;
    }}

    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stFileUploader > label,
    .stTextArea > label {{
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        color: var(--rr-text-muted) !important;
        font-family: "IBM Plex Sans", sans-serif !important;
    }}

    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploaderDropzone"] {{
        background: var(--rr-glass-bg-strong) !important;
        border: 1.5px dashed rgba(37,99,235,0.36) !important;
        border-radius: 20px !important;
        color: var(--rr-text-soft) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), 0 18px 38px var(--rr-glass-shadow) !important;
    }}

    div[data-testid="stFileUploader"] small,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] p {{
        color: var(--rr-text-muted) !important;
    }}

    .stButton > button {{
        background: var(--rr-glass-bg-strong) !important;
        color: var(--rr-text) !important;
        border: 1px solid var(--rr-border) !important;
        border-radius: 16px !important;
        font-family: "Manrope", sans-serif !important;
        font-size: 14px !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 22px var(--rr-glass-shadow) !important;
        transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease !important;
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);
        border-color: rgba(37,99,235,0.30) !important;
        box-shadow: 0 14px 28px var(--rr-glass-shadow-strong) !important;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        font-family: "Manrope", sans-serif !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 14px 30px rgba(37,99,235,0.28) !important;
    }}

    button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        box-shadow: 0 18px 34px rgba(37,99,235,0.34) !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        background: var(--rr-card-bg) !important;
        border: 1px solid var(--rr-glass-border) !important;
        border-radius: 24px !important;
        box-shadow: 0 20px 45px var(--rr-glass-shadow), inset 0 1px 0 rgba(255,255,255,0.22) !important;
        backdrop-filter: blur(14px) saturate(130%);
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head):hover,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head):hover {{
        box-shadow: 0 24px 50px var(--rr-glass-shadow-strong), inset 0 1px 0 rgba(255,255,255,0.26) !important;
    }}

    div[data-testid="stExpander"] {{
        background: var(--rr-card-bg-alt) !important;
        border: 1px solid var(--rr-border) !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 24px var(--rr-glass-shadow) !important;
    }}

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p {{
        color: var(--rr-text-muted) !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        font-family: "IBM Plex Sans", sans-serif !important;
    }}

    div[data-testid="stExpanderDetails"] p,
    div[data-testid="stExpanderDetails"] span {{
        color: var(--rr-text-soft) !important;
    }}

    div[data-testid="stChatMessage"] {{
        background: var(--rr-card-bg-alt) !important;
        border: 1px solid var(--rr-border) !important;
        border-radius: 20px !important;
        box-shadow: 0 12px 24px var(--rr-glass-shadow) !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {{
        color: var(--rr-text) !important;
    }}

    div[data-testid="stChatMessage"][data-testid*="ChatMessage-user"],
    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) {{
        background: rgba(37,99,235,0.08) !important;
        border-color: rgba(37,99,235,0.16) !important;
    }}

    div[data-testid="stChatInput"] > div {{
        background: var(--rr-glass-bg-strong) !important;
        border: 1px solid var(--rr-border) !important;
        border-radius: 18px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.18) !important;
    }}

    div[data-testid="stChatInput"] textarea {{
        color: var(--rr-text) !important;
        background: transparent !important;
        font-family: "IBM Plex Sans", sans-serif !important;
    }}

    div[data-testid="stVideo"] {{
        background: #020617 !important;
        border: 1px solid rgba(148,163,184,0.16) !important;
        border-radius: 24px !important;
        overflow: hidden !important;
        padding: 10px !important;
        box-shadow: 0 20px 40px rgba(2,6,23,0.30) !important;
    }}

    div[data-testid="stVideo"] video {{
        border-radius: 16px !important;
        display: block !important;
    }}

    .stDownloadButton > button {{
        background: var(--rr-glass-bg-strong) !important;
        color: var(--rr-accent) !important;
        border: 1px solid var(--rr-border) !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        font-family: "Manrope", sans-serif !important;
        box-shadow: 0 10px 20px var(--rr-glass-shadow) !important;
    }}

    .stCaptionContainer,
    .stCaptionContainer p {{
        color: var(--rr-text-muted) !important;
        font-family: "IBM Plex Sans", sans-serif !important;
    }}

    .stSpinner > div {{
        border-top-color: var(--rr-accent) !important;
    }}

    .rr-page-hero {{
        position: relative;
        overflow: hidden;
        display: flex;
        justify-content: space-between;
        gap: 20px;
        padding: 28px 30px;
        margin-bottom: 20px;
        border-radius: 30px;
        color: #ffffff;
        background: linear-gradient(135deg, var(--rr-hero-from), var(--rr-hero-via) 58%, var(--rr-hero-to));
        border: 1px solid rgba(255,255,255,0.10);
        box-shadow: 0 28px 64px rgba(15,23,42,0.24);
    }}

    .rr-page-hero::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 20% 0%, var(--rr-hero-highlight), transparent 34%),
            linear-gradient(120deg, rgba(255,255,255,0.10), transparent 46%);
        pointer-events: none;
    }}

    .rr-page-hero__body,
    .rr-page-hero__meta {{
        position: relative;
        z-index: 1;
    }}

    .rr-page-hero__eyebrow {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.72);
        margin-bottom: 10px;
    }}

    .rr-page-hero__title {{
        font-family: "Manrope", sans-serif;
        font-size: clamp(30px, 4vw, 44px);
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.02;
        margin: 0 0 10px;
    }}

    .rr-page-hero__copy {{
        max-width: 60ch;
        font-size: 15px;
        line-height: 1.7;
        color: rgba(255,255,255,0.82);
    }}

    .rr-page-hero__pills {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 18px;
    }}

    .rr-page-hero__pill {{
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.14);
    }}

    .rr-page-hero__meta {{
        min-width: 280px;
        max-width: 320px;
        align-self: stretch;
        padding: 18px 20px;
        border-radius: 22px;
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.12);
        backdrop-filter: blur(14px);
    }}

    .rr-page-hero__status-label,
    .rr-pane-head__eyebrow,
    .rr-section-kicker,
    .rr-kicker {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-family: "IBM Plex Sans", sans-serif;
    }}

    .rr-page-hero__status-label {{
        color: rgba(255,255,255,0.68);
        margin-bottom: 10px;
    }}

    .rr-page-hero__status-value {{
        font-family: "Manrope", sans-serif;
        font-size: 22px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 8px;
    }}

    .rr-page-hero__status-copy {{
        font-size: 13px;
        line-height: 1.65;
        color: rgba(255,255,255,0.80);
    }}

    .rr-pane-head {{
        margin-bottom: 16px;
    }}

    .rr-pane-head__eyebrow,
    .rr-section-kicker {{
        color: var(--rr-text-muted);
        margin-bottom: 6px;
    }}

    .rr-pane-head__title,
    .rr-coach-shell-head__title,
    .rr-coach-composer-intro__title,
    .rr-coach-history-intro__title,
    .rr-hero-card__title,
    .rr-dialog-hero__title {{
        font-family: "Manrope", sans-serif;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: var(--rr-text);
        line-height: 1.08;
    }}

    .rr-pane-head__copy,
    .rr-coach-composer-intro__copy,
    .rr-coach-history-intro__copy {{
        font-size: 14px;
        line-height: 1.65;
        color: var(--rr-text-muted);
        max-width: 62ch;
        margin-top: 6px;
    }}

    .rr-kicker--light {{
        color: rgba(255,255,255,0.72);
        margin-bottom: 6px;
    }}

    .rr-session-row,
    .rr-metric-card,
    .rr-fault-row,
    .rr-assistant-note,
    .rr-empty-card,
    .rr-callout,
    .rr-dialog-hero,
    .rr-compare-strip,
    .rr-comparison-shell,
    .rr-comparison-metric,
    .rr-quality-badge,
    .rr-glass-card {{
        background: var(--rr-card-bg-alt);
        border: 1px solid var(--rr-border);
        box-shadow: 0 16px 32px var(--rr-glass-shadow);
    }}

    .rr-session-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        border-radius: 18px;
        color: var(--rr-text-soft);
        font-size: 14px;
        font-weight: 600;
    }}

    .rr-session-row__arrow {{
        color: var(--rr-accent);
        font-size: 16px;
    }}

    .rr-mini-empty {{
        padding: 18px;
        border-radius: 18px;
        border: 1px dashed var(--rr-border);
        background: var(--rr-card-bg-alt);
        color: var(--rr-text-muted);
        font-size: 14px;
        line-height: 1.65;
    }}

    .rr-metric-card {{
        text-align: center;
        border-radius: 18px;
        padding: 22px 12px;
    }}

    .rr-metric-card__label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--rr-text-muted);
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .rr-metric-card__value {{
        font-size: 28px;
        font-family: "Manrope", sans-serif;
        font-weight: 800;
        color: var(--rr-text);
    }}

    .rr-fault-row {{
        padding: 12px 14px;
        margin-bottom: 8px;
        border-radius: 16px;
        font-size: 14px;
        line-height: 1.6;
        color: var(--rr-text-soft);
    }}

    .rr-fault-row--comparison {{
        background: rgba(37,99,235,0.08) !important;
        border-color: rgba(37,99,235,0.16) !important;
    }}

    .rr-hero-card {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(30,64,175,0.94));
        border-radius: 24px;
        padding: 22px 22px 18px;
        color: #ffffff;
        box-shadow: 0 22px 48px rgba(15,23,42,0.28);
        margin-bottom: 14px;
        border: 1px solid rgba(255,255,255,0.10);
    }}

    .rr-hero-card::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at top left, rgba(255,255,255,0.16), transparent 28%),
            linear-gradient(120deg, rgba(255,255,255,0.08), transparent 40%);
        pointer-events: none;
    }}

    .rr-hero-card__head {{
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: flex-start;
    }}

    .rr-hero-card__copy {{
        font-size: 14px;
        color: rgba(255,255,255,0.88);
        line-height: 1.65;
        max-width: 46ch;
    }}

    .rr-hero-card__score {{
        min-width: 96px;
        text-align: right;
    }}

    .rr-hero-card__score-value {{
        font-size: 38px;
        font-family: "Manrope", sans-serif;
        font-weight: 800;
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
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.01em;
    }}

    .rr-chip--hero {{
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.22);
        color: #ffffff;
    }}

    .rr-chip--compare {{
        background: var(--rr-glass-bg-strong);
        border: 1px solid var(--rr-border);
        color: var(--rr-text-soft);
    }}

    .rr-chip--compare-good {{
        background: rgba(34,197,94,0.10);
        color: var(--rr-success);
        border-color: rgba(34,197,94,0.18);
    }}

    .rr-chip--compare-bad {{
        background: rgba(239,68,68,0.10);
        color: var(--rr-error);
        border-color: rgba(239,68,68,0.18);
    }}

    .rr-chip--compare-neutral {{
        background: rgba(37,99,235,0.08);
        color: var(--rr-text-soft);
        border-color: rgba(37,99,235,0.16);
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
        letter-spacing: 0.12em;
        color: var(--rr-text-muted);
        font-weight: 700;
        margin-bottom: 8px;
    }}

    .rr-comparison-metric__delta {{
        font-size: 26px;
        font-family: "Manrope", sans-serif;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 8px;
        color: var(--rr-text);
    }}

    .rr-comparison-metric__delta-label {{
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--rr-text-muted);
        font-weight: 700;
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
        color: var(--rr-success);
    }}

    .rr-comparison-metric--bad .rr-comparison-metric__delta {{
        color: var(--rr-error);
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
        width: 32px;
        height: 32px;
        border-radius: 12px;
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.22);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        flex-shrink: 0;
    }}

    .rr-hero-step__title {{
        font-size: 13px;
        font-weight: 700;
        color: #ffffff;
    }}

    .rr-hero-step__desc {{
        font-size: 12px;
        color: rgba(255,255,255,0.82);
        line-height: 1.5;
    }}

    .rr-dialog-hero {{
        border-radius: 18px;
        padding: 18px 18px 16px;
        margin-bottom: 16px;
    }}

    .rr-dialog-hero__head {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
    }}

    .rr-dialog-hero__load {{
        font-size: 13px;
        font-weight: 700;
        color: var(--rr-accent);
    }}

    .rr-quality-badge {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 28px 20px 22px;
        border-radius: 18px;
        margin-bottom: 14px;
    }}

    .rr-quality-badge__title {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--rr-text-muted);
        font-weight: 700;
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
        font-family: "Manrope", sans-serif;
        font-weight: 800;
        line-height: 1;
    }}

    .rr-quality-badge__scale {{
        font-size: 10px;
        color: var(--rr-text-muted);
        margin-top: 2px;
    }}

    .rr-quality-badge__zone {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 4px 18px;
        border: 1px solid transparent;
        font-size: 13px;
        font-weight: 700;
        min-height: 32px;
    }}

    .rr-empty-card {{
        padding: 28px 24px;
        text-align: center;
        border-radius: 18px;
        font-size: 14px;
        color: var(--rr-text-muted);
        line-height: 1.7;
        border-style: dashed;
    }}

    .rr-empty-card__icon {{
        font-size: 32px;
        margin-bottom: 12px;
    }}

    .rr-empty-card--results {{
        padding: 40px 28px;
        margin: 4px 0;
    }}

    .rr-empty-card__icon--large {{
        font-size: 40px;
        margin-bottom: 14px;
    }}

    .rr-empty-card__title {{
        font-size: 17px;
        font-family: "Manrope", sans-serif;
        font-weight: 800;
        color: var(--rr-text);
        margin-bottom: 8px;
    }}

    .rr-empty-card__body {{
        max-width: 42ch;
        margin: 0 auto;
        line-height: 1.7;
    }}

    .rr-callout {{
        display: flex;
        gap: 12px;
        align-items: flex-start;
        padding: 12px 14px;
        margin: 10px 0;
        border-radius: 16px;
        background: var(--rr-callout-bg);
        border: 1px solid var(--rr-callout-color);
        color: var(--rr-text-soft);
        font-size: 14px;
        line-height: 1.6;
    }}

    .rr-callout__icon {{
        width: 22px;
        height: 22px;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        background: var(--rr-callout-color);
        color: #ffffff;
        font-family: "Manrope", sans-serif;
        font-size: 12px;
        font-weight: 800;
        margin-top: 1px;
    }}

    .rr-callout__body {{
        flex: 1;
        white-space: pre-line;
    }}

    .rr-assistant-note {{
        padding: 14px 16px;
        border-radius: 18px;
        font-size: 14px;
        line-height: 1.7;
        color: var(--rr-text-soft);
    }}

    .rr-coach-shell-head {{
        margin-bottom: 14px;
        padding-bottom: 14px;
        border-bottom: 1px solid var(--rr-border);
    }}

    /* Refined app shell: calmer hierarchy, replay-first layout, lighter inline surfaces */
    [data-testid="stToolbar"],
    [data-testid="stToolbarActions"],
    .stAppToolbar {{
        display: none !important;
    }}

    :root,
    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    section[data-testid="stMain"] {{
        color-scheme: only dark !important;
    }}

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    section[data-testid="stMain"],
    section[data-testid="stMain"] > div {{
        background:
            radial-gradient(circle at 15% 0%, rgba(67, 97, 238, 0.18), transparent 28%),
            radial-gradient(circle at 78% 2%, rgba(56, 189, 248, 0.10), transparent 22%),
            linear-gradient(180deg, #0a1630 0%, #081223 48%, #060f1d 100%) !important;
        background-color: #081223 !important;
    }}

    .block-container {{
        position: relative;
        max-width: 1420px !important;
        padding-top: 26px !important;
        padding-bottom: 32px !important;
    }}

    .block-container::before {{
        content: "";
        position: absolute;
        inset: 14px 10px 14px 12px;
        border-radius: 34px;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.02), transparent 30%),
            rgba(8, 17, 31, 0.42);
        border: 1px solid rgba(148,163,184,0.08);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        pointer-events: none;
    }}

    .block-container > * {{
        position: relative;
        z-index: 1;
    }}

    [data-testid="stSidebar"] {{
        background:
            radial-gradient(circle at 16% 0%, rgba(96,165,250,0.16), transparent 26%),
            linear-gradient(180deg, #0a1530 0%, #081122 100%) !important;
        box-shadow:
            inset -1px 0 0 rgba(255,255,255,0.05),
            18px 0 40px rgba(2,6,23,0.12) !important;
    }}

    .rr-sidebar-brand {{
        padding: 14px 14px 16px;
        margin: 2px 0 18px;
        border-radius: 24px;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.03), transparent 36%),
            rgba(8, 17, 31, 0.36);
        border: 1px solid rgba(116, 147, 195, 0.12);
    }}

    .rr-sidebar-brand__mark {{
        width: 46px;
        height: 46px;
        border-radius: 16px;
        background:
            radial-gradient(circle at 30% 25%, rgba(255,255,255,0.24), transparent 26%),
            linear-gradient(135deg, #5b8cff, #1d4ed8 62%, #0f172a);
        box-shadow:
            0 14px 28px rgba(37,99,235,0.20),
            inset 0 1px 0 rgba(255,255,255,0.18);
    }}

    [data-testid="stSidebar"] .stButton > button {{
        background: rgba(9, 18, 33, 0.74) !important;
        border: 1px solid rgba(116, 147, 195, 0.12) !important;
        border-radius: 18px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04) !important;
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(12, 22, 40, 0.86) !important;
        border-color: rgba(148, 163, 184, 0.18) !important;
        box-shadow:
            0 12px 24px rgba(2,6,23,0.14),
            inset 0 1px 0 rgba(255,255,255,0.06) !important;
    }}

    .stTextInput > label,
    .stNumberInput > label,
    .stSelectbox > label,
    .stFileUploader > label,
    .stTextArea > label {{
        font-size: 10.5px !important;
        letter-spacing: 0.10em !important;
        color: #91a6c7 !important;
    }}

    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 16px !important;
        box-shadow: none !important;
        transform: none !important;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        box-shadow: none !important;
        transform: none !important;
    }}

    button[kind="primary"] {{
        background:
            linear-gradient(135deg, #7bb0ff 0%, #5f97fb 45%, #4d87f6 100%) !important;
        color: #f8fbff !important;
        border: 1px solid rgba(147, 197, 253, 0.26) !important;
        box-shadow:
            0 16px 32px rgba(37,99,235,0.20),
            inset 0 1px 0 rgba(255,255,255,0.26) !important;
    }}

    button[kind="primary"]:hover {{
        background:
            linear-gradient(135deg, #8abcff 0%, #6aa0ff 45%, #5b92ff 100%) !important;
        box-shadow:
            0 18px 36px rgba(37,99,235,0.22),
            inset 0 1px 0 rgba(255,255,255,0.30) !important;
    }}

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div,
    .stSelectbox > div > div,
    div[data-testid="stChatInput"] > div {{
        background: #0e1930 !important;
        background-color: #0e1930 !important;
        border: 1px solid rgba(125, 149, 189, 0.18) !important;
        color: #e7eefb !important;
        -webkit-text-fill-color: #e7eefb !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 0 0 1px rgba(6,15,29,0.12) !important;
        border-radius: 16px !important;
    }}

    .stTextArea textarea,
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {{
        padding-top: 12px !important;
        padding-bottom: 12px !important;
    }}

    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {{
        color: #7f93b6 !important;
        -webkit-text-fill-color: #7f93b6 !important;
    }}

    div[data-baseweb="select"] span,
    div[data-baseweb="select"] svg,
    .stSelectbox * {{
        color: #e7eefb !important;
    }}

    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploaderDropzone"] {{
        min-height: 108px !important;
        background: linear-gradient(180deg, rgba(14,25,48,0.98), rgba(12,21,39,0.96)) !important;
        border: 1px solid rgba(91, 132, 208, 0.28) !important;
        border-radius: 18px !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.04),
            0 10px 20px rgba(2, 6, 23, 0.12) !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }}

    .rr-stage-shell,
    .rr-library-shell,
    .rr-analysis-bar-shell,
    .rr-context-shell,
    .rr-history-shell {{
        width: 0;
        height: 0;
        overflow: hidden;
        opacity: 0;
        pointer-events: none;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-stage-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) {{
        position: relative;
        background:
            radial-gradient(circle at 12% 0%, rgba(96,165,250,0.12), transparent 34%),
            linear-gradient(180deg, rgba(10,19,35,0.98), rgba(8,16,29,0.96)) !important;
        border: 1px solid rgba(116, 147, 195, 0.14) !important;
        border-radius: 30px !important;
        box-shadow:
            0 24px 54px rgba(2, 6, 23, 0.22),
            inset 0 1px 0 rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(8px) saturate(120%);
        overflow: hidden !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-stage-shell)::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 78% 18%, rgba(59,130,246,0.08), transparent 24%),
            linear-gradient(180deg, rgba(255,255,255,0.03), transparent 18%);
        pointer-events: none;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        position: relative;
        background:
            radial-gradient(circle at top right, rgba(96,165,250,0.10), transparent 26%),
            linear-gradient(180deg, rgba(11,21,39,0.96), rgba(8,17,31,0.94)) !important;
        border: 1px solid rgba(116, 147, 195, 0.14) !important;
        border-radius: 28px !important;
        box-shadow:
            0 22px 50px rgba(2, 6, 23, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(10px) saturate(120%);
        overflow: hidden !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head)::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(180deg, rgba(255,255,255,0.03), transparent 20%),
            radial-gradient(circle at 78% 4%, rgba(59,130,246,0.08), transparent 18%);
        pointer-events: none;
    }}

    div[data-testid="stExpander"] {{
        background:
            linear-gradient(180deg, rgba(14,23,41,0.96), rgba(10,18,33,0.96)) !important;
        border: 1px solid rgba(116, 147, 195, 0.14) !important;
        border-radius: 20px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04) !important;
    }}

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p {{
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.10em !important;
        text-transform: uppercase !important;
        color: var(--rr-text-muted) !important;
    }}

    .rr-app-header {{
        position: relative;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 20px 22px;
        margin: 0 0 22px;
        border-radius: 28px;
        border: 1px solid rgba(116, 147, 195, 0.14);
        background:
            radial-gradient(circle at 0% 0%, rgba(96,165,250,0.12), transparent 26%),
            linear-gradient(180deg, rgba(12,22,41,0.96), rgba(9,18,34,0.92));
        box-shadow:
            0 24px 50px rgba(2, 6, 23, 0.18),
            inset 0 1px 0 rgba(255,255,255,0.05);
        overflow: hidden;
    }}

    .rr-app-header::before {{
        content: "";
        position: absolute;
        inset: 0;
        background:
            radial-gradient(circle at 82% 10%, rgba(59,130,246,0.10), transparent 18%),
            linear-gradient(90deg, rgba(255,255,255,0.04), transparent 35%);
        pointer-events: none;
    }}

    .rr-app-header__main,
    .rr-app-header__meta {{
        position: relative;
        z-index: 1;
    }}

    .rr-app-header__title {{
        font-family: "Manrope", sans-serif;
        font-size: clamp(28px, 3.2vw, 40px);
        font-weight: 800;
        line-height: 1.04;
        letter-spacing: -0.04em;
        color: var(--rr-text);
        margin: 6px 0 8px;
    }}

    .rr-app-header__copy {{
        max-width: 64ch;
        font-size: 15px;
        line-height: 1.7;
        color: #b6c5dd;
    }}

    .rr-app-header__tags {{
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 14px;
    }}

    .rr-app-header__tag {{
        display: inline-flex;
        align-items: center;
        min-height: 32px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid rgba(116, 147, 195, 0.16);
        background: rgba(11, 22, 41, 0.72);
        color: #bfd3f7;
        font-size: 12px;
        font-weight: 700;
    }}

    .rr-app-header__meta {{
        display: flex;
        flex-direction: row;
        gap: 10px;
        align-items: center;
        justify-content: flex-end;
        min-width: 260px;
        flex-wrap: wrap;
    }}

    .rr-app-header__status,
    .rr-app-header__submeta {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 36px;
        padding: 0 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.01em;
    }}

    .rr-app-header__status {{
        background: rgba(76, 132, 255, 0.12);
        border: 1px solid rgba(96, 165, 250, 0.18);
        color: #9cc3ff;
    }}

    .rr-app-header__submeta {{
        background: rgba(11, 22, 41, 0.78);
        border: 1px solid rgba(116, 147, 195, 0.14);
        color: #a6b7d4;
    }}

    .rr-pane-head {{
        margin-bottom: 14px;
    }}

    .rr-pane-head--stage {{
        margin-bottom: 20px;
    }}

    .rr-pane-head--stage .rr-pane-head__title {{
        font-size: clamp(22px, 3vw, 34px);
        line-height: 1.02;
    }}

    .rr-pane-head--stage .rr-pane-head__copy {{
        max-width: 52ch;
        color: #b4c4dd;
    }}

    .rr-pane-head--stage .rr-pane-head__eyebrow {{
        color: #9ed7ff;
    }}

    .rr-library-copy {{
        margin: 2px 0 14px;
        font-size: 13px;
        line-height: 1.6;
        color: #aab9d2;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: clamp(340px, 54vh, 720px) !important;
        aspect-ratio: 16 / 9;
        background:
            radial-gradient(circle at 50% 0%, rgba(59,130,246,0.08), transparent 28%),
            #08101c !important;
        border: 1px solid rgba(116, 147, 195, 0.14) !important;
        border-radius: 24px !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.03),
            0 18px 32px rgba(2, 6, 23, 0.16) !important;
        overflow: hidden !important;
        padding: 14px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] video {{
        width: 100% !important;
        max-height: min(70vh, 760px) !important;
        object-fit: contain !important;
        background: #030814 !important;
        border-radius: 18px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card--results {{
        min-height: clamp(340px, 54vh, 720px);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background:
            radial-gradient(circle at 50% 0%, rgba(59,130,246,0.09), transparent 28%),
            linear-gradient(180deg, rgba(8,17,29,0.99), rgba(8,17,29,0.94));
        border: 1px solid rgba(116, 147, 195, 0.14);
        border-style: solid;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card__title {{
        color: #f8fafc;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card__body {{
        color: #94a3b8;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
        margin: 10px 0 14px;
        padding: 18px 18px 10px;
        border-radius: 24px;
        border: 1px solid rgba(116, 147, 195, 0.12);
        background:
            linear-gradient(180deg, rgba(255,255,255,0.02), transparent 24%),
            rgba(8, 17, 31, 0.38);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-context-shell) {{
        margin-top: 12px;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid rgba(116, 147, 195, 0.10);
    }}

    .rr-analysis-bar-head,
    .rr-coach-history-intro {{
        margin: 0 0 14px;
        padding: 0 0 2px;
        border-bottom: none;
    }}

    .rr-analysis-bar-head__title,
    .rr-coach-history-intro__title {{
        font-family: "Manrope", sans-serif;
        font-size: 19px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--rr-text);
    }}

    .rr-analysis-bar-head__copy,
    .rr-coach-history-intro__copy {{
        margin-top: 6px;
        font-size: 13px;
        line-height: 1.6;
        color: #aebed7;
    }}

    .rr-coach-shell-head {{
        margin-bottom: 16px;
        padding-bottom: 0;
        border-bottom: none;
    }}

    .rr-coach-shell-head__title {{
        font-size: 24px;
    }}

    .rr-session-row,
    .rr-fault-row,
    .rr-assistant-note,
    .rr-mini-empty,
    .rr-callout,
    div[data-testid="stChatMessage"] {{
        box-shadow: none !important;
    }}

    .rr-session-row {{
        padding: 12px 14px;
        margin-bottom: 8px;
        border: 1px solid rgba(116, 147, 195, 0.10);
        border-radius: 16px;
        background: rgba(10, 18, 33, 0.52);
    }}

    .rr-mini-empty {{
        padding: 16px 14px;
        border: 1px dashed rgba(116, 147, 195, 0.14);
        border-radius: 16px;
        background: rgba(10, 18, 33, 0.32);
    }}

    .rr-metric-card,
    .rr-quality-badge,
    .rr-comparison-shell,
    .rr-comparison-metric,
    .rr-compare-strip,
    .rr-dialog-hero {{
        background: var(--rr-card-bg-alt);
        border: 1px solid rgba(148,163,184,0.14);
        box-shadow: none;
    }}

    .rr-fault-row,
    .rr-assistant-note {{
        background: rgba(10, 18, 33, 0.58);
        border: 1px solid rgba(116, 147, 195, 0.10);
    }}

    .rr-callout {{
        gap: 10px;
        background: linear-gradient(180deg, rgba(10,18,33,0.78), rgba(10,18,33,0.72));
        border: 1px solid rgba(116, 147, 195, 0.10);
        border-left: 3px solid var(--rr-callout-color);
        border-radius: 16px;
    }}

    .rr-hero-card {{
        background:
            radial-gradient(circle at top left, rgba(96,165,250,0.10), transparent 28%),
            linear-gradient(180deg, rgba(255,255,255,0.02), transparent 30%),
            rgba(12, 22, 40, 0.90);
        border: 1px solid rgba(116, 147, 195, 0.12);
        box-shadow:
            0 20px 40px rgba(2, 6, 23, 0.12),
            inset 0 1px 0 rgba(255,255,255,0.05);
        color: var(--rr-text);
    }}

    .rr-hero-card::before {{
        background:
            linear-gradient(90deg, rgba(37,99,235,0.08), transparent 42%);
    }}

    .rr-hero-card__copy,
    .rr-hero-step__desc,
    .rr-comparison-summary,
    .rr-compare-strip__summary,
    .rr-comparison-note {{
        color: var(--rr-text-soft);
    }}

    .rr-kicker--light {{
        color: var(--rr-text-muted);
    }}

    .rr-hero-card__score {{
        min-width: 0;
        text-align: left;
    }}

    .rr-hero-card__score-value,
    .rr-hero-card__score-scale,
    .rr-hero-card__title,
    .rr-hero-step__title {{
        color: var(--rr-text);
    }}

    .rr-hero-step__icon {{
        background: rgba(76, 132, 255, 0.10);
        border: 1px solid rgba(96, 165, 250, 0.16);
        color: #93c5fd;
    }}

    .rr-chip--hero {{
        background: rgba(76, 132, 255, 0.08);
        border: 1px solid rgba(96, 165, 250, 0.14);
        color: #c6d7f4;
    }}

    div[data-testid="stChatMessage"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 0 12px !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
        padding: 13px 15px !important;
        border-radius: 20px 20px 20px 12px !important;
        border: 1px solid rgba(116, 147, 195, 0.10) !important;
        background: linear-gradient(180deg, rgba(12,22,40,0.84), rgba(10,18,33,0.80)) !important;
    }}

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stMarkdownContainer"] {{
        border-radius: 20px 20px 12px 20px !important;
        background: linear-gradient(180deg, rgba(52, 103, 205, 0.22), rgba(40, 83, 170, 0.20)) !important;
        border-color: rgba(96,165,250,0.16) !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {{
        margin-bottom: 0 !important;
    }}

    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}

    ::-webkit-scrollbar-thumb {{
        background: rgba(148,163,184,0.36);
        border-radius: 999px;
    }}

    @media (max-width: 1100px) {{
        .rr-app-header {{
            flex-direction: column;
            align-items: flex-start;
        }}

        .rr-app-header__meta {{
            align-items: flex-start;
            justify-content: flex-start;
            min-width: 0;
        }}
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding-top: 18px !important;
            padding-left: 16px !important;
            padding-right: 16px !important;
        }}

        .block-container::before {{
            inset: 10px 6px;
            border-radius: 24px;
        }}

        div[data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
            gap: 0.75rem !important;
        }}

        div[data-testid="stHorizontalBlock"] > div {{
            min-width: 100% !important;
            width: 100% !important;
        }}

        .rr-app-header {{
            gap: 14px;
            margin-bottom: 14px;
            padding: 18px 16px;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head),
        div[data-testid="stExpander"] {{
            border-radius: 18px !important;
            backdrop-filter: none !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card--results {{
            min-height: 240px !important;
            aspect-ratio: auto;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] video {{
            max-height: 52vh !important;
        }}

        .rr-hero-card__head,
        .rr-dialog-hero__head {{
            flex-direction: column;
            align-items: flex-start;
        }}

        .rr-pane-head__copy,
        .rr-analysis-bar-head__copy,
        .rr-coach-history-intro__copy {{
            max-width: none;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
            padding: 16px 14px 8px;
            border-radius: 20px;
        }}
    }}

    /* Bolder visual shift: remove the giant frame, open the replay stage, and make the coach pane warmer */
    .block-container::before {{
        display: none !important;
    }}

    .block-container {{
        max-width: 1480px !important;
        padding-top: 24px !important;
        padding-left: 34px !important;
        padding-right: 34px !important;
        background: transparent !important;
    }}

    .rr-app-header {{
        align-items: flex-start;
        padding: 2px 2px 18px;
        margin: 0 0 26px;
        border: none;
        border-radius: 0;
        background: transparent;
        box-shadow: none;
        overflow: visible;
    }}

    .rr-app-header::before {{
        display: none;
    }}

    .rr-app-header__title {{
        font-size: clamp(34px, 4vw, 52px);
        line-height: 0.98;
        letter-spacing: -0.05em;
        margin: 8px 0 10px;
    }}

    .rr-app-header__copy {{
        max-width: 46ch;
        font-size: 16px;
        line-height: 1.72;
        color: #c6d5ea;
    }}

    .rr-app-header__tags {{
        margin-top: 18px;
    }}

    .rr-app-header__tag {{
        min-height: 34px;
        padding: 0 14px;
        background: rgba(20, 33, 58, 0.72);
        border-color: rgba(122, 150, 194, 0.18);
        color: #d3e4ff;
        backdrop-filter: blur(10px);
    }}

    .rr-app-header__meta {{
        gap: 12px;
        min-width: 0;
        padding-top: 10px;
    }}

    .rr-app-header__status,
    .rr-app-header__submeta {{
        min-height: 40px;
        padding: 0 15px;
        font-size: 12.5px;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-stage-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        overflow: visible !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-stage-shell)::before {{
        display: none !important;
    }}

    .rr-pane-head--stage {{
        padding: 8px 6px 0;
        margin-bottom: 18px;
    }}

    .rr-pane-head--stage .rr-pane-head__title {{
        font-size: clamp(26px, 3.3vw, 40px);
    }}

    .rr-pane-head--stage .rr-pane-head__copy {{
        max-width: 42ch;
        font-size: 16px;
        line-height: 1.7;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"],
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card--results {{
        min-height: clamp(380px, 58vh, 760px) !important;
        background:
            radial-gradient(circle at 50% 0%, rgba(56,189,248,0.10), transparent 24%),
            radial-gradient(circle at 82% 100%, rgba(251,146,60,0.08), transparent 24%),
            linear-gradient(180deg, rgba(8,15,28,0.98), rgba(6,12,22,0.98)) !important;
        border: 1px solid rgba(122, 150, 194, 0.16) !important;
        border-radius: 32px !important;
        box-shadow:
            0 28px 56px rgba(2,6,23,0.24),
            inset 0 1px 0 rgba(255,255,255,0.05),
            inset 0 0 0 1px rgba(255,255,255,0.02) !important;
        padding: 18px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] video {{
        border-radius: 22px !important;
    }}

    div[data-testid="stExpander"] {{
        background: rgba(15, 25, 44, 0.42) !important;
        border: 1px solid rgba(122, 150, 194, 0.14) !important;
        border-radius: 999px !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }}

    div[data-testid="stExpanderDetails"] {{
        padding: 0 18px 14px 18px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        background:
            radial-gradient(circle at top right, rgba(96,165,250,0.14), transparent 26%),
            radial-gradient(circle at left bottom, rgba(14,165,233,0.06), transparent 20%),
            linear-gradient(180deg, rgba(14,24,43,0.97), rgba(9,17,31,0.95)) !important;
        border: 1px solid rgba(122, 150, 194, 0.16) !important;
        border-radius: 30px !important;
        box-shadow:
            0 30px 60px rgba(2,6,23,0.22),
            inset 0 1px 0 rgba(255,255,255,0.05) !important;
    }}

    .rr-coach-shell-head {{
        padding: 4px 4px 14px;
        margin-bottom: 18px;
    }}

    .rr-coach-shell-head__title {{
        font-size: 25px;
        letter-spacing: -0.04em;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
        margin: 6px 0 18px;
        padding: 20px 20px 12px;
        border-radius: 28px;
        border: 1px solid rgba(122, 150, 194, 0.14);
        background:
            radial-gradient(circle at top left, rgba(96,165,250,0.10), transparent 28%),
            linear-gradient(180deg, rgba(20, 36, 64, 0.72), rgba(12, 23, 42, 0.82));
        box-shadow:
            0 18px 34px rgba(2,6,23,0.16),
            inset 0 1px 0 rgba(255,255,255,0.05);
    }}

    .rr-analysis-bar-head__title {{
        font-size: 20px;
    }}

    .rr-analysis-bar-head__copy {{
        max-width: 50ch;
        color: #bfcee6;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-context-shell) {{
        margin-top: 8px;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        margin-top: 20px;
        padding-top: 18px;
        border-top: 1px solid rgba(122, 150, 194, 0.10);
    }}

    .rr-session-row {{
        padding: 13px 16px;
        border-radius: 18px;
        background:
            linear-gradient(180deg, rgba(17, 29, 50, 0.74), rgba(12, 22, 39, 0.70));
    }}

    .rr-mini-empty {{
        padding: 18px 16px;
        border-radius: 18px;
        background:
            linear-gradient(180deg, rgba(17, 29, 50, 0.54), rgba(12, 22, 39, 0.44));
    }}

    .rr-callout,
    .rr-fault-row,
    .rr-assistant-note,
    .rr-metric-card,
    .rr-quality-badge,
    .rr-comparison-shell,
    .rr-comparison-metric,
    .rr-compare-strip,
    .rr-dialog-hero {{
        border-color: rgba(122, 150, 194, 0.12);
    }}

    .rr-hero-card {{
        border-radius: 28px;
        background:
            radial-gradient(circle at top left, rgba(96,165,250,0.12), transparent 28%),
            linear-gradient(180deg, rgba(255,255,255,0.02), transparent 24%),
            rgba(13, 24, 44, 0.92);
    }}

    button[kind="primary"] {{
        border-radius: 18px !important;
        min-height: 56px !important;
        font-size: 16px !important;
        font-weight: 800 !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
        padding: 14px 16px !important;
        border-radius: 22px 22px 22px 14px !important;
        background:
            linear-gradient(180deg, rgba(16, 28, 48, 0.90), rgba(12, 22, 39, 0.84)) !important;
    }}

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stMarkdownContainer"] {{
        border-radius: 22px 22px 14px 22px !important;
        background:
            linear-gradient(180deg, rgba(73, 125, 230, 0.30), rgba(47, 87, 175, 0.24)) !important;
    }}

    @media (max-width: 1100px) {{
        .rr-app-header {{
            gap: 16px;
        }}

        .rr-app-header__meta {{
            padding-top: 0;
        }}
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding-left: 16px !important;
            padding-right: 16px !important;
        }}

        .rr-app-header {{
            padding: 4px 0 14px;
            margin-bottom: 18px;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card--results {{
            min-height: 280px !important;
            border-radius: 24px !important;
            padding: 12px !important;
        }}

        div[data-testid="stExpander"] {{
            border-radius: 22px !important;
        }}
    }}

    /* Final shell system: replay-first layout with fewer framed subsections */
    .rr-nav-shell,
    .rr-stage-shell,
    .rr-coach-workspace-shell,
    .rr-analysis-bar-shell,
    .rr-context-shell,
    .rr-history-shell,
    .rr-library-shell {{
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-nav-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-stage-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-workspace-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-analysis-bar-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-context-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-history-shell),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-library-shell) {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }}

    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {{
        display: block !important;
    }}

    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }}

    .rr-app-header {{
        padding-bottom: 14px;
        margin-bottom: 22px;
        border-bottom: 1px solid rgba(122, 150, 194, 0.12);
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) {{
        position: sticky !important;
        top: 20px !important;
        align-self: flex-start !important;
        padding: 4px 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    .rr-sidebar-brand--rail {{
        margin: 0 0 16px;
        padding: 16px 14px;
        border-radius: 24px;
        background:
            linear-gradient(180deg, rgba(18,31,55,0.86), rgba(12,22,39,0.82));
        border: 1px solid rgba(122, 150, 194, 0.12);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) .stButton > button {{
        min-height: 46px !important;
        border-radius: 16px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0 14px !important;
        background: rgba(13, 23, 41, 0.66) !important;
        border: 1px solid rgba(122, 150, 194, 0.10) !important;
        color: #e5eefb !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) .stButton > button:hover {{
        background: rgba(18, 31, 55, 0.82) !important;
        border-color: rgba(122, 150, 194, 0.16) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) .stButton > button[kind="primary"] {{
        justify-content: center !important;
        text-align: center !important;
    }}

    .rr-nav-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0 16px;
    }}

    .rr-nav-meta__pill,
    .rr-nav-label {{
        font-size: 10.5px;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }}

    .rr-nav-meta__pill {{
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0 10px;
        border-radius: 999px;
        background: rgba(18, 31, 55, 0.56);
        border: 1px solid rgba(122, 150, 194, 0.10);
        color: #9eb6da;
    }}

    .rr-nav-label {{
        margin: 10px 0 8px;
        color: #85a0c8;
    }}

    .rr-app-header__copy {{
        max-width: 42ch;
        font-size: 15px;
    }}

    .rr-app-header__tags {{
        margin-top: 14px;
    }}

    .rr-app-header__tag {{
        min-height: 32px;
        padding: 0 13px;
        background: rgba(18, 31, 55, 0.62);
        border-color: rgba(122, 150, 194, 0.14);
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) {{
        padding: 2px 0 10px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-pane-head--stage {{
        padding: 2px 2px 0 !important;
        margin-bottom: 14px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"],
    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-empty-card--results {{
        min-height: clamp(440px, 64vh, 820px) !important;
        border-radius: 32px !important;
        border: 1px solid rgba(122, 150, 194, 0.14) !important;
        background:
            radial-gradient(circle at 50% 0%, rgba(56,189,248,0.11), transparent 24%),
            radial-gradient(circle at 85% 100%, rgba(251,146,60,0.08), transparent 20%),
            linear-gradient(180deg, rgba(8,15,28,0.98), rgba(5,11,20,0.99)) !important;
        box-shadow:
            0 34px 68px rgba(2,6,23,0.26),
            inset 0 1px 0 rgba(255,255,255,0.05) !important;
        padding: 18px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] video {{
        border-radius: 22px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] > div {{
        width: 100% !important;
        display: flex !important;
        justify-content: center !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] video {{
        display: block !important;
        width: auto !important;
        max-width: min(100%, 1120px) !important;
        max-height: 72vh !important;
        height: auto !important;
        margin: 0 auto !important;
        object-fit: contain !important;
        background: transparent !important;
    }}

    div[data-testid="stExpander"] {{
        background: rgba(13, 22, 40, 0.46) !important;
        border: 1px solid rgba(122, 150, 194, 0.10) !important;
        border-radius: 22px !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }}

    div[data-testid="stExpander"] summary {{
        min-height: 54px;
    }}

    div[data-testid="stExpanderDetails"] {{
        padding: 0 18px 16px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell) {{
        padding: 2px 0 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell)::before {{
        display: none !important;
    }}

    .rr-coach-shell-head {{
        margin-bottom: 12px;
        padding: 0 2px 4px;
        border-bottom: 1px solid rgba(122, 150, 194, 0.10);
    }}

    .rr-coach-shell-head__title {{
        font-size: 24px;
        letter-spacing: -0.04em;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
        margin: 6px 0 14px !important;
        padding: 16px 16px 8px !important;
        border-radius: 22px !important;
        background:
            linear-gradient(180deg, rgba(22,38,66,0.84), rgba(14,24,43,0.78)) !important;
        border: 1px solid rgba(122, 150, 194, 0.12) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,0.05),
            0 12px 24px rgba(2,6,23,0.10) !important;
    }}

    .rr-analysis-bar-head {{
        margin-bottom: 12px;
    }}

    .rr-analysis-bar-head__title {{
        font-size: 18px;
    }}

    .rr-analysis-bar-head__copy,
    .rr-pane-head__copy,
    .rr-library-copy,
    .rr-history-head__copy,
    .rr-summary-strip__copy,
    .rr-workspace-hint__copy,
    .rr-workspace-hint__step-desc {{
        color: #c4d2e7 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-context-shell) {{
        margin: 0 0 12px !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        margin-top: 8px !important;
        padding-top: 12px !important;
        border-top: 1px solid rgba(122, 150, 194, 0.08) !important;
        background: transparent !important;
    }}

    .rr-summary-strip {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 14px;
        padding: 16px 16px 14px;
        border-radius: 20px;
        background:
            linear-gradient(180deg, rgba(18,31,54,0.78), rgba(13,24,43,0.74));
        border: 1px solid rgba(122, 150, 194, 0.11);
    }}

    .rr-summary-strip--comparison {{
        margin-top: 10px;
        display: block;
        padding-bottom: 12px;
    }}

    .rr-summary-strip__main {{
        min-width: 0;
        flex: 1;
    }}

    .rr-summary-strip__title {{
        margin-top: 4px;
        font-family: "Manrope", sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #f5f9ff;
    }}

    .rr-summary-strip__copy {{
        margin-top: 6px;
        font-size: 13px;
        line-height: 1.65;
    }}

    .rr-summary-strip__score {{
        min-width: 72px;
        text-align: right;
    }}

    .rr-summary-strip__score-label {{
        display: block;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: #90a7cc;
    }}

    .rr-summary-strip__score-value {{
        margin-top: 4px;
        font-family: "Manrope", sans-serif;
        font-size: 28px;
        font-weight: 800;
        line-height: 1;
        color: #f8fbff;
    }}

    .rr-chip-row--compact {{
        margin-top: 10px;
        gap: 8px;
    }}

    .rr-workspace-hint {{
        padding: 16px 16px 14px;
        border-radius: 20px;
        background:
            linear-gradient(180deg, rgba(17,29,50,0.60), rgba(12,22,39,0.56));
        border: 1px solid rgba(122, 150, 194, 0.10);
    }}

    .rr-workspace-hint__title {{
        margin-top: 4px;
        font-family: "Manrope", sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #f5f9ff;
    }}

    .rr-workspace-hint__copy {{
        margin-top: 6px;
        font-size: 13px;
        line-height: 1.65;
    }}

    .rr-workspace-hint__grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
        margin-top: 14px;
    }}

    .rr-workspace-hint__step {{
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }}

    .rr-workspace-hint__icon {{
        width: 30px;
        height: 30px;
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: rgba(76, 132, 255, 0.10);
        border: 1px solid rgba(96, 165, 250, 0.14);
        color: #95c5ff;
        flex: 0 0 auto;
    }}

    .rr-workspace-hint__step-title {{
        font-size: 13px;
        font-weight: 700;
        color: #e9f1ff;
    }}

    .rr-workspace-hint__step-desc {{
        margin-top: 3px;
        font-size: 12.5px;
        line-height: 1.55;
    }}

    .rr-workspace-hint__tip {{
        margin-top: 12px;
        font-size: 12px;
        line-height: 1.6;
        color: #8ea4c9;
    }}

    .rr-history-head {{
        margin-bottom: 10px;
        padding: 0 2px;
    }}

    .rr-history-head__title {{
        margin-top: 4px;
        font-family: "Manrope", sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #f5f9ff;
    }}

    .rr-history-head__copy {{
        margin-top: 6px;
        font-size: 13px;
        line-height: 1.6;
    }}

    .rr-session-row,
    .rr-mini-empty {{
        background:
            linear-gradient(180deg, rgba(18,30,52,0.62), rgba(13,23,41,0.58)) !important;
        border: 1px solid rgba(122, 150, 194, 0.09) !important;
    }}

    .rr-hero-card,
    .rr-callout,
    .rr-metric-card,
    .rr-quality-badge,
    .rr-comparison-shell,
    .rr-comparison-metric,
    .rr-compare-strip,
    .rr-dialog-hero,
    .rr-fault-row,
    .rr-assistant-note {{
        box-shadow: none !important;
    }}

    .rr-callout,
    .rr-fault-row,
    .rr-assistant-note {{
        border-radius: 16px;
    }}

    div[data-testid="stChatMessage"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 0 10px !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
        padding: 13px 15px !important;
        border-radius: 18px 18px 18px 12px !important;
        border: 1px solid rgba(122, 150, 194, 0.09) !important;
        background: linear-gradient(180deg, rgba(16,28,48,0.82), rgba(12,22,39,0.78)) !important;
    }}

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stMarkdownContainer"] {{
        border-radius: 18px 18px 12px 18px !important;
        background: linear-gradient(180deg, rgba(66, 116, 219, 0.24), rgba(46, 85, 170, 0.20)) !important;
        border-color: rgba(96,165,250,0.14) !important;
    }}

    /* ChatGPT-like shell pass: use the canvas, slim the rail, and keep the experience calmer */
    .block-container {{
        width: calc(100vw - 12px) !important;
        max-width: none !important;
        padding-top: 14px !important;
        padding-left: 8px !important;
        padding-right: 8px !important;
        padding-bottom: 18px !important;
    }}

    html,
    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    section[data-testid="stMain"],
    section[data-testid="stMain"] > div {{
        background:
            radial-gradient(circle at 12% 0%, rgba(56, 189, 248, 0.08), transparent 24%),
            radial-gradient(circle at 88% 0%, rgba(59, 130, 246, 0.10), transparent 20%),
            linear-gradient(180deg, #09111f 0%, #0b1322 50%, #0a111e 100%) !important;
    }}

    .rr-app-header {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        align-items: start;
        gap: 18px;
        padding: 4px 0 0;
        margin-bottom: 18px;
        border-bottom: none;
    }}

    .rr-app-header__title {{
        font-size: clamp(42px, 5vw, 64px);
        line-height: 0.94;
        letter-spacing: -0.055em;
        margin: 6px 0 10px;
    }}

    .rr-app-header__copy {{
        max-width: 54ch;
        font-size: 15px;
        line-height: 1.72;
        color: #b8c6db;
    }}

    .rr-app-header__meta {{
        display: grid;
        justify-items: end;
        gap: 10px;
        padding-top: 6px;
    }}

    .rr-app-header__status-group {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: flex-end;
    }}

    .rr-hero-visual {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 10px 14px 8px;
        border-radius: 18px;
        background: rgba(13, 22, 39, 0.54);
        border: 1px solid rgba(122, 150, 194, 0.08);
    }}

    .rr-hero-visual .rr-lift-loop {{
        margin-bottom: 0;
    }}

    .rr-hero-visual__label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #8ea6ca;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) {{
        top: 16px !important;
        min-width: 240px !important;
        width: 100% !important;
    }}

    .rr-sidebar-brand--rail {{
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        gap: 12px;
        align-items: start;
        padding: 14px 12px;
        border-radius: 20px;
        background: rgba(12, 20, 35, 0.84);
        border: 1px solid rgba(122, 150, 194, 0.10);
    }}

    .rr-sidebar-brand--rail .rr-sidebar-brand__name {{
        font-size: 30px;
        line-height: 1;
    }}

    .rr-sidebar-brand--rail .rr-sidebar-brand__copy {{
        max-width: none;
        font-size: 13px;
        line-height: 1.55;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) .stButton > button {{
        min-height: 42px !important;
        border-radius: 14px !important;
        font-size: 14px !important;
        background: rgba(14, 23, 40, 0.72) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) .stButton > button[kind="primary"] {{
        min-height: 54px !important;
        border-radius: 18px !important;
        background: linear-gradient(135deg, #7ab3ff 0%, #5f96fb 48%, #4c87f6 100%) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"],
    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-empty-card--results {{
        min-height: clamp(500px, 72vh, 900px) !important;
        border-radius: 34px !important;
        padding: 24px !important;
    }}

    .rr-pane-head--stage .rr-pane-head__title {{
        font-size: clamp(30px, 3.8vw, 48px);
    }}

    .rr-pane-head--stage .rr-pane-head__copy {{
        max-width: 38ch;
        font-size: 15px;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell) {{
        padding-top: 10px !important;
    }}

    .rr-coach-shell-head {{
        margin-bottom: 10px;
        padding-bottom: 6px;
    }}

    .rr-coach-shell-head__title {{
        font-size: 22px;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
        margin: 4px 0 14px !important;
        padding: 18px 18px 12px !important;
        border-radius: 24px !important;
        background: rgba(16, 27, 47, 0.82) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextArea textarea {{
        min-height: 120px !important;
        border-radius: 18px !important;
        background: rgba(14, 22, 39, 0.90) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) div[data-testid="stFileUploaderDropzone"] {{
        background: rgba(13, 22, 40, 0.88) !important;
        border-radius: 18px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        margin-top: 10px !important;
        padding-top: 14px !important;
    }}

    .rr-history-head {{
        margin-bottom: 8px;
    }}

    .rr-summary-strip,
    .rr-workspace-hint {{
        background: rgba(15, 24, 41, 0.64);
        border-color: rgba(122, 150, 194, 0.08);
    }}

    .rr-empty-card {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    .rr-empty-card--results {{
        gap: 18px;
        text-align: center;
    }}

    .rr-empty-card__title {{
        max-width: 24ch;
        margin: 0 auto;
        font-size: clamp(28px, 3vw, 38px);
        letter-spacing: -0.04em;
    }}

    .rr-empty-card__body {{
        max-width: 40ch;
        margin: 0 auto;
        font-size: 14px;
        line-height: 1.8;
    }}

    div[data-testid="stChatMessage"] {{
        margin: 0 0 12px !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
        max-width: 94%;
        padding: 10px 0 !important;
        border-radius: 0 !important;
        border: none !important;
        background: transparent !important;
    }}

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stMarkdownContainer"] {{
        max-width: 86%;
        margin-left: auto;
        padding: 12px 16px !important;
        border-radius: 18px !important;
        background: rgba(29, 48, 84, 0.76) !important;
        border: 1px solid rgba(122, 150, 194, 0.10) !important;
    }}

    @media (min-width: 1101px) {{
        .block-container {{
            min-height: 100vh !important;
        }}

        div[data-testid="stHorizontalBlock"]:has(.rr-nav-shell) > div:first-child {{
            min-width: 250px !important;
            max-width: 290px !important;
            flex: 0 0 clamp(250px, 16vw, 290px) !important;
        }}

        div[data-testid="stHorizontalBlock"]:not(:has(.rr-nav-shell)) > div:first-child {{
            min-width: 0 !important;
            max-width: none !important;
            flex: 1 1 auto !important;
        }}

        div[data-testid="stHorizontalBlock"] {{
            align-items: flex-start !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) {{
            position: sticky !important;
            top: 12px !important;
            max-height: calc(100vh - 24px) !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding-right: 6px !important;
            scrollbar-gutter: stable;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell) {{
            position: sticky !important;
            top: 12px !important;
            max-height: calc(100vh - 24px) !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
            min-height: 0 !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell),
        div[data-testid="stVerticalBlock"]:has(.rr-context-shell) {{
            flex: 0 0 auto !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding-right: 6px !important;
            margin-right: -2px !important;
            scrollbar-gutter: stable;
        }}

        div[data-testid="stExpanderDetails"] {{
            max-height: 34vh !important;
            overflow-y: auto !important;
            scrollbar-gutter: stable;
        }}
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {{
        font-size: 14px !important;
        line-height: 1.7 !important;
    }}

    .rr-lift-loop {{
        position: relative;
        width: min(320px, 72vw);
        height: 128px;
        margin: 0 auto 8px;
    }}

    .rr-lift-loop--compact {{
        width: 112px;
        height: 54px;
        margin-bottom: 10px;
        transform: scale(0.9);
        transform-origin: center;
    }}

    .rr-lift-loop__platform {{
        position: absolute;
        left: 10%;
        right: 10%;
        bottom: 18px;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(122, 150, 194, 0.24), transparent);
    }}

    .rr-lift-loop__barbell {{
        position: absolute;
        left: 18%;
        right: 18%;
        top: 22px;
        height: 4px;
        border-radius: 999px;
        background: linear-gradient(90deg, #4fd1ff, #9cc3ff, #4fd1ff);
        box-shadow: 0 0 18px rgba(79, 209, 255, 0.18);
        animation: rr-lift-bar 2.4s ease-in-out infinite;
    }}

    .rr-lift-loop__plate {{
        position: absolute;
        top: 12px;
        width: 18px;
        height: 24px;
        border-radius: 9px;
        background: rgba(166, 196, 255, 0.16);
        border: 1px solid rgba(156, 195, 255, 0.34);
        animation: rr-lift-bar 2.4s ease-in-out infinite;
    }}

    .rr-lift-loop__plate--left {{
        left: 16%;
    }}

    .rr-lift-loop__plate--right {{
        right: 16%;
    }}

    .rr-lift-loop__athlete {{
        position: absolute;
        left: 50%;
        bottom: 22px;
        width: 82px;
        height: 82px;
        transform: translateX(-50%);
        animation: rr-lift-athlete 2.4s ease-in-out infinite;
    }}

    .rr-lift-loop__head,
    .rr-lift-loop__torso,
    .rr-lift-loop__arm,
    .rr-lift-loop__leg {{
        position: absolute;
        background: #dce8ff;
        border-radius: 999px;
    }}

    .rr-lift-loop__head {{
        width: 14px;
        height: 14px;
        left: 34px;
        top: 6px;
        background: #f4f8ff;
    }}

    .rr-lift-loop__torso {{
        width: 6px;
        height: 28px;
        left: 38px;
        top: 20px;
    }}

    .rr-lift-loop__arm {{
        width: 28px;
        height: 4px;
        top: 28px;
    }}

    .rr-lift-loop__arm--left {{
        left: 12px;
        transform: rotate(-18deg);
        transform-origin: right center;
    }}

    .rr-lift-loop__arm--right {{
        right: 12px;
        transform: rotate(18deg);
        transform-origin: left center;
    }}

    .rr-lift-loop__leg {{
        width: 24px;
        height: 4px;
        top: 54px;
    }}

    .rr-lift-loop__leg--left {{
        left: 18px;
        transform: rotate(22deg);
        transform-origin: right center;
    }}

    .rr-lift-loop__leg--right {{
        right: 18px;
        transform: rotate(-22deg);
        transform-origin: left center;
    }}

    .rr-lift-loop__wave {{
        position: absolute;
        border: 1px solid rgba(79, 209, 255, 0.16);
        border-radius: 999px;
        opacity: 0;
    }}

    .rr-lift-loop__wave--one {{
        inset: 18px 58px 34px;
        animation: rr-lift-wave 2.4s ease-out infinite;
    }}

    .rr-lift-loop__wave--two {{
        inset: 8px 40px 20px;
        animation: rr-lift-wave 2.4s ease-out 0.4s infinite;
    }}

    @keyframes rr-lift-bar {{
        0%, 100% {{ transform: translateY(20px); }}
        35% {{ transform: translateY(0); }}
        60% {{ transform: translateY(2px); }}
    }}

    @keyframes rr-lift-athlete {{
        0%, 100% {{ transform: translateX(-50%) translateY(10px); }}
        35% {{ transform: translateX(-50%) translateY(0); }}
        60% {{ transform: translateX(-50%) translateY(2px); }}
    }}

    @keyframes rr-lift-wave {{
        0% {{ opacity: 0; transform: scale(0.94); }}
        30% {{ opacity: 1; }}
        100% {{ opacity: 0; transform: scale(1.08); }}
    }}

    @media (max-width: 900px) {{
        div[data-testid="stVerticalBlock"]:has(.rr-nav-shell) {{
            position: static !important;
            margin-bottom: 8px !important;
            max-height: none !important;
            overflow: visible !important;
        }}

        .block-container {{
            width: calc(100vw - 6px) !important;
            max-width: none !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
        }}

        .rr-app-header {{
            margin-bottom: 18px;
            grid-template-columns: 1fr;
        }}

        .rr-app-header__title {{
            font-size: clamp(34px, 10vw, 46px);
        }}

        .rr-app-header__meta {{
            justify-items: start;
        }}

        .rr-app-header__status-group {{
            justify-content: flex-start;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell) {{
            position: static !important;
            max-height: none !important;
            overflow: visible !important;
            padding: 20px 16px 16px !important;
            border-radius: 24px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
            padding: 14px 14px 8px !important;
            border-radius: 18px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"],
        div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-empty-card--results {{
            min-height: 300px !important;
            border-radius: 24px !important;
        }}

        .rr-summary-strip {{
            flex-direction: column;
        }}

        .rr-summary-strip__score {{
            text-align: left;
        }}

        .rr-lift-loop {{
            width: min(250px, 76vw);
            height: 108px;
        }}
    }}

    /* Final contrast guardrails for the coach workspace */
    div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell),
    div[data-testid="stVerticalBlock"]:has(.rr-context-shell),
    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        color: #eef4ff !important;
    }}

    .rr-coach-shell-head__title,
    .rr-analysis-bar-head__title,
    .rr-history-head__title,
    .rr-summary-strip__title,
    .rr-workspace-hint__title,
    .rr-workspace-hint__step-title,
    .rr-empty-card__title {{
        color: #f5f9ff !important;
    }}

    .rr-analysis-bar-head__copy,
    .rr-history-head__copy,
    .rr-summary-strip__copy,
    .rr-workspace-hint__copy,
    .rr-workspace-hint__step-desc,
    .rr-workspace-hint__tip,
    .rr-empty-card__body,
    .rr-empty-card,
    .rr-summary-strip__score-label,
    .rr-nav-meta__pill,
    .rr-nav-label {{
        color: #cfdced !important;
    }}

    .rr-summary-strip__score-value,
    .rr-workspace-hint__icon,
    .rr-empty-card__icon {{
        color: #eef4ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) label,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) [data-testid="stWidgetLabel"],
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stSelectbox label,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stNumberInput label,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stFileUploader label {{
        color: #dbe7f7 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextArea textarea,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextInput input,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stNumberInput input,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stSelectbox div[data-baseweb="select"] * {{
        color: #eef4ff !important;
        -webkit-text-fill-color: #eef4ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextArea textarea::placeholder,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextInput input::placeholder,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stNumberInput input::placeholder {{
        color: #96abc9 !important;
        -webkit-text-fill-color: #96abc9 !important;
        opacity: 1 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) div[data-testid="stFileUploaderDropzone"],
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) div[data-testid="stFileUploaderDropzone"] * {{
        color: #d8e5f7 !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {{
        color: #e8f1ff !important;
    }}

    div[data-testid="stChatMessage"] small,
    div[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] {{
        color: #9fb2ce !important;
    }}

    /* Final replay / summary polish */
    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"],
    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-empty-card--results {{
        min-height: clamp(560px, 78vh, 980px) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] video {{
        max-width: min(100%, 1320px) !important;
        max-height: 80vh !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-context-shell) [data-testid="stColumn"] > div {{
        height: 100% !important;
    }}

    .rr-summary-strip {{
        min-height: 100% !important;
    }}

    .rr-quality-badge {{
        min-height: 210px !important;
        height: 100% !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
    }}

    .rr-quality-badge__ring {{
        margin: 0 auto !important;
    }}

    /* Final analysis dialog emphasis */
    .rr-dialog-hero {{
        border-radius: 24px !important;
        padding: 22px 24px 20px !important;
        background:
            radial-gradient(circle at top right, rgba(96, 165, 250, 0.10), transparent 28%),
            linear-gradient(180deg, rgba(15, 24, 41, 0.94), rgba(11, 18, 31, 0.96)) !important;
        border-color: rgba(122, 150, 194, 0.14) !important;
    }}

    .rr-dialog-hero__title {{
        font-size: clamp(32px, 4vw, 42px) !important;
        line-height: 0.98 !important;
    }}

    .rr-dialog-hero__load {{
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(96, 165, 250, 0.22);
        background: rgba(25, 68, 152, 0.18);
        color: #8fc3ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) {{
        margin: 0 0 18px !important;
        padding: 22px 22px 18px !important;
        border-radius: 28px !important;
        background:
            radial-gradient(circle at top left, rgba(96, 165, 250, 0.10), transparent 28%),
            linear-gradient(180deg, rgba(15, 24, 41, 0.92), rgba(11, 18, 31, 0.96)) !important;
        border: 1px solid rgba(122, 150, 194, 0.14) !important;
        box-shadow: 0 22px 48px rgba(2, 6, 23, 0.22) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) div[data-testid="stHorizontalBlock"] {{
        align-items: stretch !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) .rr-quality-badge {{
        margin-bottom: 0 !important;
        min-height: 100% !important;
        border-radius: 24px !important;
        padding: 28px 22px 24px !important;
        background: linear-gradient(180deg, rgba(16, 28, 48, 0.86), rgba(11, 19, 33, 0.92)) !important;
        border-color: rgba(122, 150, 194, 0.16) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge {{
        margin-bottom: 0 !important;
        min-height: 100% !important;
        border-radius: 24px !important;
        padding: 28px 22px 24px !important;
        background: linear-gradient(180deg, rgba(16, 28, 48, 0.86), rgba(11, 19, 33, 0.92)) !important;
        border-color: rgba(122, 150, 194, 0.16) !important;
    }}

    .rr-quality-badge--hero .rr-quality-badge__title {{
        font-size: 12px !important;
        letter-spacing: 0.14em !important;
        margin-bottom: 18px !important;
    }}

    .rr-quality-badge--hero .rr-quality-badge__ring {{
        width: 152px !important;
        height: 152px !important;
        margin-bottom: 18px !important;
    }}

    .rr-quality-badge--hero .rr-quality-badge__value {{
        font-size: 48px !important;
    }}

    .rr-quality-badge--hero .rr-quality-badge__scale {{
        font-size: 11px !important;
        margin-top: 4px !important;
    }}

    .rr-quality-badge--hero .rr-quality-badge__zone {{
        padding: 8px 18px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }}

    .rr-analysis-overview-copy {{
        margin: 2px 0 14px;
        padding: 2px 2px 4px;
    }}

    .rr-analysis-overview-copy__kicker {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--rr-text-muted);
        margin-bottom: 8px;
    }}

    .rr-analysis-overview-copy__title {{
        font-family: "Manrope", sans-serif;
        font-size: clamp(24px, 2.4vw, 30px);
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.04;
        color: #f4f8ff;
        margin-bottom: 8px;
    }}

    .rr-analysis-overview-copy__body {{
        max-width: 54ch;
        font-size: 14px;
        line-height: 1.7;
        color: #cdd9ea;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) .rr-metric-card {{
        min-height: 150px !important;
        padding: 24px 16px !important;
        border-radius: 22px !important;
        background: linear-gradient(180deg, rgba(16, 27, 47, 0.88), rgba(12, 20, 35, 0.92)) !important;
        border-color: rgba(122, 150, 194, 0.12) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) .rr-metric-card__label {{
        color: #9eb4d4 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) .rr-metric-card__value {{
        font-size: clamp(30px, 3vw, 38px) !important;
        color: #f5f9ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__title {{
        font-size: 12px !important;
        letter-spacing: 0.14em !important;
        margin-bottom: 18px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__ring {{
        width: 152px !important;
        height: 152px !important;
        margin: 0 auto 18px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__ring svg {{
        width: 152px !important;
        height: 152px !important;
        display: block !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__value {{
        font-size: 48px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__scale {{
        font-size: 11px !important;
        margin-top: 4px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__zone {{
        padding: 8px 18px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-reply-shell) {{
        margin-top: 18px !important;
        padding: 18px 18px 14px !important;
        border-radius: 22px !important;
        background: linear-gradient(180deg, rgba(14, 23, 40, 0.84), rgba(11, 18, 31, 0.92)) !important;
        border: 1px solid rgba(122, 150, 194, 0.12) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-reply-shell) [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-reply-shell) [data-testid="stMarkdownContainer"] li {{
        color: #e8f1ff !important;
        line-height: 1.75 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-reply-shell) [data-testid="stMarkdownContainer"] strong {{
        color: #f5f9ff !important;
    }}

    @media (max-width: 900px) {{
        div[data-testid="stVerticalBlock"]:has(.rr-analysis-overview-shell) {{
            padding: 16px 16px 12px !important;
            border-radius: 22px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__ring {{
            width: 132px !important;
            height: 132px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__ring svg {{
            width: 132px !important;
            height: 132px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-analysis-badge-hero-shell) .rr-quality-badge__value {{
            font-size: 42px !important;
        }}

        .rr-quality-badge--hero .rr-quality-badge__ring {{
            width: 132px !important;
            height: 132px !important;
        }}

        .rr-quality-badge--hero .rr-quality-badge__value {{
            font-size: 42px !important;
        }}
    }}

    /* Final stage / coach balance */
    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-pane-head--stage {{
        max-width: 100% !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) .rr-pane-head--stage .rr-pane-head__copy {{
        max-width: 52ch !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] {{
        min-height: clamp(540px, 72vh, 920px) !important;
        padding: 14px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] > div {{
        width: 100% !important;
        justify-content: center !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] video {{
        width: 100% !important;
        max-width: 100% !important;
        max-height: 78vh !important;
        height: auto !important;
        object-fit: contain !important;
        margin: 0 auto !important;
        background: #030814 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-analysis-shell) {{
        margin-top: 14px !important;
        padding: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-analysis-shell) .rr-summary-strip,
    div[data-testid="stVerticalBlock"]:has(.rr-stage-analysis-shell) .rr-quality-badge {{
        background: linear-gradient(180deg, rgba(16, 28, 48, 0.88), rgba(12, 21, 38, 0.92)) !important;
        border-color: rgba(122, 150, 194, 0.12) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-stage-analysis-shell) .stButton > button,
    div[data-testid="stVerticalBlock"]:has(.rr-stage-analysis-shell) .stDownloadButton > button {{
        min-height: 46px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-coach-workspace-shell) {{
        max-width: 100% !important;
        padding-left: 0 !important;
    }}

    .rr-coach-shell-head__title {{
        font-size: 18px !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) {{
        padding: 14px 14px 10px !important;
        border-radius: 22px !important;
    }}

    .rr-analysis-bar-head__title {{
        font-size: 17px !important;
        line-height: 1.22 !important;
    }}

    .rr-analysis-bar-head__copy {{
        max-width: 42ch !important;
    }}

    .rr-pane-head__copy,
    .rr-coach-shell-head,
    .rr-analysis-bar-head__copy,
    .rr-summary-strip__copy,
    .rr-workspace-hint__copy,
    .rr-workspace-hint__step-desc,
    .rr-workspace-hint__tip {{
        color: #d7e3f3 !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextArea textarea,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextInput input,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stNumberInput input,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) div[data-baseweb="select"] > div {{
        background: rgba(11, 19, 33, 0.92) !important;
        border-color: rgba(122, 150, 194, 0.20) !important;
        color: #f4f8ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextArea textarea::placeholder,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stTextInput input::placeholder,
    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) .stNumberInput input::placeholder {{
        color: #adc0da !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-analysis-bar-shell) div[data-testid="stFileUploaderDropzone"] {{
        background: rgba(10, 18, 32, 0.90) !important;
        border-color: rgba(96, 165, 250, 0.34) !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) [data-testid="stMarkdownContainer"] p,
    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) [data-testid="stMarkdownContainer"] li,
    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) [data-testid="stCaptionContainer"] p {{
        color: #eaf2ff !important;
    }}

    div[data-testid="stVerticalBlock"]:has(.rr-history-shell) {{
        margin-top: 12px !important;
        padding-top: 14px !important;
        border-top: 1px solid rgba(122, 150, 194, 0.10) !important;
    }}

    @media (max-width: 900px) {{
        div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] {{
            min-height: 360px !important;
            padding: 12px !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.rr-stage-shell) div[data-testid="stVideo"] video {{
            max-height: 58vh !important;
        }}
    }}
    </style>
    """
