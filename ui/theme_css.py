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
        z-index: 1000 !important;
    }}

    [data-testid="collapsedControl"] > button,
    [data-testid="stSidebarCollapsedControl"] > button {{
        background: var(--rr-sidebar-bg) !important;
        color: var(--rr-sidebar-text) !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 0 16px 16px 0 !important;
        box-shadow: 0 12px 30px rgba(2,6,23,0.28) !important;
    }}

    [data-testid="collapsedControl"] > button:hover,
    [data-testid="stSidebarCollapsedControl"] > button:hover {{
        background: #16233a !important;
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

    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 14px !important;
        box-shadow: none !important;
        transform: none !important;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        box-shadow: none !important;
        transform: none !important;
    }}

    button[kind="primary"] {{
        background: var(--rr-accent) !important;
        box-shadow: none !important;
    }}

    button[kind="primary"]:hover {{
        background: var(--rr-accent-hover) !important;
        box-shadow: none !important;
    }}

    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea,
    div[data-baseweb="select"] > div,
    .stSelectbox > div > div,
    div[data-testid="stChatInput"] > div {{
        box-shadow: none !important;
        border-radius: 14px !important;
    }}

    div[data-testid="stFileUploader"] section,
    div[data-testid="stFileUploaderDropzone"] {{
        border-radius: 16px !important;
        box-shadow: none !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) {{
        background: linear-gradient(180deg, rgba(7,17,31,0.98), rgba(10,20,36,0.94)) !important;
        border: 1px solid rgba(148,163,184,0.14) !important;
        border-radius: 28px !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-coach-shell-head) {{
        background: var(--rr-card-bg) !important;
        border: 1px solid var(--rr-glass-border) !important;
        border-radius: 24px !important;
        box-shadow: none !important;
        backdrop-filter: blur(10px) saturate(120%);
    }}

    div[data-testid="stExpander"] {{
        background: var(--rr-card-bg) !important;
        border: 1px solid var(--rr-glass-border) !important;
        border-radius: 20px !important;
        box-shadow: none !important;
    }}

    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] summary p {{
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: var(--rr-text-muted) !important;
    }}

    .rr-app-header {{
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 20px;
        padding: 0 0 16px;
        margin: 0 0 18px;
        border-bottom: 1px solid rgba(148,163,184,0.14);
    }}

    .rr-app-header__title {{
        font-family: "Manrope", sans-serif;
        font-size: clamp(24px, 3vw, 34px);
        font-weight: 800;
        line-height: 1.04;
        letter-spacing: -0.04em;
        color: var(--rr-text);
        margin: 4px 0 6px;
    }}

    .rr-app-header__copy {{
        max-width: 64ch;
        font-size: 14px;
        line-height: 1.65;
        color: var(--rr-text-muted);
    }}

    .rr-app-header__meta {{
        display: flex;
        flex-direction: column;
        gap: 8px;
        align-items: flex-end;
        min-width: 220px;
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
        background: rgba(37,99,235,0.10);
        border: 1px solid rgba(37,99,235,0.16);
        color: var(--rr-accent);
    }}

    .rr-app-header__submeta {{
        background: rgba(148,163,184,0.08);
        border: 1px solid rgba(148,163,184,0.12);
        color: var(--rr-text-muted);
    }}

    .rr-pane-head {{
        margin-bottom: 14px;
    }}

    .rr-pane-head--stage {{
        margin-bottom: 18px;
    }}

    .rr-pane-head--stage .rr-pane-head__title {{
        font-size: clamp(20px, 2.8vw, 30px);
        line-height: 1.05;
    }}

    .rr-pane-head--stage .rr-pane-head__copy {{
        max-width: 52ch;
        color: #94a3b8;
    }}

    .rr-pane-head--stage .rr-pane-head__eyebrow {{
        color: #7dd3fc;
    }}

    .rr-library-copy {{
        margin: 2px 0 14px;
        font-size: 13px;
        line-height: 1.6;
        color: var(--rr-text-muted);
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: clamp(340px, 54vh, 720px) !important;
        aspect-ratio: 16 / 9;
        background: #08111d !important;
        border: 1px solid rgba(148,163,184,0.14) !important;
        border-radius: 22px !important;
        box-shadow: none !important;
        overflow: hidden !important;
        padding: 12px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) div[data-testid="stVideo"] video {{
        width: 100% !important;
        max-height: min(70vh, 760px) !important;
        object-fit: contain !important;
        background: #020617 !important;
        border-radius: 16px !important;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card--results {{
        min-height: clamp(340px, 54vh, 720px);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(180deg, rgba(8,17,29,0.98), rgba(8,17,29,0.92));
        border: 1px solid rgba(148,163,184,0.14);
        box-shadow: none;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card__title {{
        color: #f8fafc;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.rr-pane-head--stage) .rr-empty-card__body {{
        color: #94a3b8;
    }}

    .rr-analysis-bar-head,
    .rr-coach-history-intro {{
        margin: 0 0 12px;
        padding: 0 0 12px;
        border-bottom: 1px solid rgba(148,163,184,0.12);
    }}

    .rr-analysis-bar-head__title,
    .rr-coach-history-intro__title {{
        font-family: "Manrope", sans-serif;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: var(--rr-text);
    }}

    .rr-analysis-bar-head__copy,
    .rr-coach-history-intro__copy {{
        margin-top: 6px;
        font-size: 13px;
        line-height: 1.6;
        color: var(--rr-text-muted);
    }}

    .rr-coach-shell-head {{
        margin-bottom: 14px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(148,163,184,0.12);
    }}

    .rr-coach-shell-head__title {{
        font-size: 22px;
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
        padding: 12px 0;
        margin-bottom: 2px;
        border: none;
        border-bottom: 1px solid rgba(148,163,184,0.12);
        border-radius: 0;
        background: transparent;
    }}

    .rr-mini-empty {{
        padding: 14px 0 2px;
        border: none;
        border-top: 1px dashed rgba(148,163,184,0.16);
        border-radius: 0;
        background: transparent;
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
        background: rgba(148,163,184,0.06);
        border: 1px solid rgba(148,163,184,0.12);
    }}

    .rr-callout {{
        gap: 10px;
        background: var(--rr-callout-bg);
        border: 1px solid rgba(148,163,184,0.10);
        border-left: 3px solid var(--rr-callout-color);
        border-radius: 14px;
    }}

    .rr-hero-card {{
        background:
            linear-gradient(180deg, rgba(37,99,235,0.04), transparent 55%),
            var(--rr-card-bg-alt);
        border: 1px solid rgba(148,163,184,0.14);
        box-shadow: none;
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
        background: rgba(37,99,235,0.08);
        border: 1px solid rgba(37,99,235,0.14);
        color: var(--rr-accent);
    }}

    .rr-chip--hero {{
        background: rgba(37,99,235,0.08);
        border: 1px solid rgba(37,99,235,0.14);
        color: var(--rr-text-soft);
    }}

    div[data-testid="stChatMessage"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 0 12px !important;
    }}

    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {{
        padding: 12px 14px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(148,163,184,0.12) !important;
        background: rgba(148,163,184,0.06) !important;
    }}

    div[data-testid="stChatMessage"]:has([aria-label="user avatar"]) [data-testid="stMarkdownContainer"] {{
        background: rgba(37,99,235,0.10) !important;
        border-color: rgba(37,99,235,0.16) !important;
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
            min-width: 0;
        }}
    }}

    @media (max-width: 900px) {{
        .block-container {{
            padding-top: 18px !important;
            padding-left: 16px !important;
            padding-right: 16px !important;
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
    }}
    </style>
    """
