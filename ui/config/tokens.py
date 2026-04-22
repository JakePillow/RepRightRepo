from __future__ import annotations

EXERCISES = ["bench", "deadlift", "squat", "curl"]

EXERCISE_ICONS = {
    "bench": "🏋️",
    "deadlift": "⬆️",
    "squat": "🦵",
    "curl": "💪",
}

PAGE = {
    "title": "RepRight",
    "layout": "wide",
    "columns": [1.5, 1],
}

THEME = {
    "page_bg": "#dbe4f2",
    "page_bg_alt": "#f2f6fb",
    "stage_bg": "rgba(246, 249, 255, 0.72)",
    "stage_bg_alt": "rgba(228, 236, 248, 0.88)",
    "stage_border": "rgba(255, 255, 255, 0.72)",
    "stage_inner_border": "rgba(140, 161, 191, 0.26)",
    "stage_glow_a": "rgba(255, 255, 255, 0.86)",
    "stage_glow_b": "rgba(128, 170, 255, 0.20)",
    "pattern_line": "rgba(119, 141, 173, 0.12)",
    "card_bg": "rgba(255, 255, 255, 0.66)",
    "card_bg_alt": "rgba(246, 249, 255, 0.52)",
    "glass_bg": "rgba(255, 255, 255, 0.54)",
    "glass_bg_strong": "rgba(255, 255, 255, 0.76)",
    "glass_border": "rgba(255, 255, 255, 0.50)",
    "glass_shadow": "rgba(24, 39, 75, 0.12)",
    "glass_shadow_strong": "rgba(15, 23, 42, 0.20)",
    "hero_from": "rgba(130, 182, 255, 0.94)",
    "hero_via": "rgba(86, 134, 255, 0.92)",
    "hero_to": "rgba(31, 67, 168, 0.94)",
    "hero_highlight": "rgba(255, 255, 255, 0.30)",
    "text": "#13233a",
    "text_soft": "#233a59",
    "text_muted": "#5f7594",
    "border": "rgba(129, 151, 184, 0.28)",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_soft": "rgba(96, 165, 250, 0.24)",
    "sidebar_bg": "#102038",
    "sidebar_button": "rgba(255, 255, 255, 0.08)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.15)",
    "sidebar_text": "#eff4ff",
    "sidebar_muted": "#9bb2d0",
    "warning": "#b45309",
    "warning_bg": "#fef3c7",
    "success": "#15803d",
    "success_bg": "#dcfce7",
    "error": "#b91c1c",
    "error_bg": "#fee2e2",
}

DARK_THEME = {
    "page_bg": "#09111d",
    "page_bg_alt": "#121e31",
    "stage_bg": "rgba(12, 22, 37, 0.80)",
    "stage_bg_alt": "rgba(19, 31, 49, 0.92)",
    "stage_border": "rgba(157, 193, 255, 0.12)",
    "stage_inner_border": "rgba(147, 177, 224, 0.14)",
    "stage_glow_a": "rgba(43, 71, 119, 0.42)",
    "stage_glow_b": "rgba(62, 126, 255, 0.18)",
    "pattern_line": "rgba(165, 188, 223, 0.07)",
    "card_bg": "rgba(18, 29, 46, 0.70)",
    "card_bg_alt": "rgba(21, 35, 56, 0.54)",
    "glass_bg": "rgba(15, 26, 42, 0.58)",
    "glass_bg_strong": "rgba(17, 29, 47, 0.78)",
    "glass_border": "rgba(156, 189, 243, 0.12)",
    "glass_shadow": "rgba(2, 6, 23, 0.38)",
    "glass_shadow_strong": "rgba(2, 6, 23, 0.58)",
    "hero_from": "rgba(43, 90, 193, 0.92)",
    "hero_via": "rgba(24, 73, 176, 0.94)",
    "hero_to": "rgba(8, 31, 84, 0.98)",
    "hero_highlight": "rgba(255, 255, 255, 0.10)",
    "text": "#ecf4ff",
    "text_soft": "#d2deef",
    "text_muted": "#9cb2cf",
    "border": "rgba(152, 180, 227, 0.16)",
    "accent": "#60a5fa",
    "accent_hover": "#93c5fd",
    "accent_soft": "rgba(96, 165, 250, 0.20)",
    "sidebar_bg": "#071220",
    "sidebar_button": "rgba(255, 255, 255, 0.06)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.12)",
    "sidebar_text": "#eff4ff",
    "sidebar_muted": "#8fa9cc",
    "warning": "#f59e0b",
    "warning_bg": "rgba(245, 158, 11, 0.16)",
    "success": "#4ade80",
    "success_bg": "rgba(74, 222, 128, 0.16)",
    "error": "#f87171",
    "error_bg": "rgba(248, 113, 113, 0.16)",
}

TEXT = {
    "sidebar": {
        "new_chat": "+ New Session",
        "new_chat_help": "Start a fresh draft without removing saved sessions.",
        "clear_chat": "Clear messages",
        "clear_chat_help": "Clear the current conversation while keeping the latest analysis.",
        "sessions_header": "Sessions",
        "recent_header": "Recent Sessions",
    },
    "inputs": {
        "exercise": "Exercise",
        "exercise_locked": "Exercise is locked to this analyzed set. Start a new session to analyze a different lift.",
        "load": "Load (KG)",
        "upload": "Upload Set Video",
        "coach_note": "Note to Coach (Optional)",
        "analyze": "Analyze set →",
        "upload_warning": "Please upload a video before analyzing.",
        "busy_help": "Analysis is running. Controls will unlock when it finishes.",
    },
    "results": {
        "quality_title": "Lift Quality",
        "reps": "Reps",
        "avg_rom": "Avg ROM",
        "low_confidence": "Low conf. reps",
        "why_score": "Form Breakdown",
        "no_faults": "No recurring faults detected — clean set.",
        "download_json": "⬇  Export analysis JSON",
    },
    "chat": {
        "follow_up": "Ask your coach anything...",
        "follow_up_disabled": "Run an analysis to ask follow-up questions.",
    },
    "states": {
        "empty_title": "No analysis results yet.",
        "empty_body": "Upload a video of a set and get feedback on your form, metrics, and potential improvements.",
        "empty_results": "Upload a video and run an analysis to see your form score, detailed metrics, and AI coaching in this pane.",
    },
    "progress": {
        "tracking": "Tracking pose…",
        "context": "Building coach context…",
        "coach": "Generating coaching response…",
        "done": "Done.",
    },
    "errors": {
        "analysis_failed": "Analysis failed. Please try again with another upload or review the error details below.",
        "followup_failed": "Follow-up coaching failed. Please try sending your question again.",
        "details_prefix": "Details:",
    },
    "coaching_panel": {
        "title": "Coaching Overview",
        "subtitle": "Upload a video and run an analysis\nto see your form score, detailed\nmetrics, and AI coaching in this pane.",
        "how_title": "How it Works",
        "view_all": "View all",
        "tip": "Tip: Side views work best for analyzing most exercises.",
        "steps": [
            ("📷", "Camera Pose Estimation", "AI analyzes your movement."),
            ("✅", "Form Assessment", "Get rep breakdown and metrics."),
            ("💬", "Coaching Feedback", "Receive personalized AI guidance."),
        ],
    },
    "main_title": "Analyze Your Set",
    "recent_sessions_title": "Recent Sessions",
}

QUALITY_ZONES = {
    "none": {"color": "#64748b", "label": "No data", "bg": "#f1f5f9", "ring": "#cbd5e1"},
    "green": {"color": "#16a34a", "label": "Good form", "bg": "#dcfce7", "ring": "#86efac"},
    "yellow": {"color": "#d97706", "label": "Needs work", "bg": "#fef3c7", "ring": "#fcd34d"},
    "red": {"color": "#dc2626", "label": "Poor form", "bg": "#fee2e2", "ring": "#fca5a5"},
}

FAULT_SEVERITY_COLORS = {
    "critical": ("#dc2626", "#fee2e2"),
    "high": ("#ea580c", "#ffedd5"),
    "medium": ("#d97706", "#fef3c7"),
    "warning": ("#d97706", "#fef3c7"),
    "info": ("#64748b", "#f1f5f9"),
}

EMPTY_STATES = {
    "video": "No overlay yet. Run an analysis to generate a pose-annotated replay.",
    "chat": "Ask about your form after running an analysis.",
}

SECTION_FLAGS = {
    "left_input_panel": True,
    "left_overlay_panel": True,
    "right_results_header": True,
    "right_results_metrics": True,
    "right_faults": True,
    "right_artifacts": True,
    "right_chat": True,
}
