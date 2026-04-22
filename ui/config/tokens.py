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
    # Wii/WiiU light palette
    "page_bg": "#EEF4FF",
    "page_bg_alt": "#FFFFFF",
    "stage_bg": "rgba(255, 255, 255, 0.88)",
    "stage_bg_alt": "rgba(238, 244, 255, 0.96)",
    "stage_border": "rgba(255, 255, 255, 0.90)",
    "stage_inner_border": "rgba(0, 102, 204, 0.14)",
    "stage_glow_a": "rgba(255, 255, 255, 0.92)",
    "stage_glow_b": "rgba(77, 179, 255, 0.18)",
    "pattern_line": "rgba(0, 87, 183, 0.06)",
    "card_bg": "rgba(255, 255, 255, 0.90)",
    "card_bg_alt": "rgba(238, 244, 255, 0.72)",
    "glass_bg": "rgba(255, 255, 255, 0.70)",
    "glass_bg_strong": "rgba(255, 255, 255, 0.94)",
    "glass_border": "rgba(0, 102, 204, 0.18)",
    "glass_shadow": "rgba(0, 30, 80, 0.10)",
    "glass_shadow_strong": "rgba(0, 30, 80, 0.18)",
    "hero_from": "rgba(77, 179, 255, 0.96)",
    "hero_via": "rgba(0, 102, 204, 0.96)",
    "hero_to": "rgba(0, 63, 138, 0.98)",
    "hero_highlight": "rgba(255, 255, 255, 0.38)",
    "text": "#001E50",
    "text_soft": "#0057B7",
    "text_muted": "#4A7ABF",
    "border": "rgba(0, 87, 183, 0.20)",
    "accent": "#0057B7",
    "accent_hover": "#003F8A",
    "accent_soft": "rgba(0, 102, 204, 0.14)",
    "sidebar_bg": "#001E50",
    "sidebar_button": "rgba(255, 255, 255, 0.10)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.20)",
    "sidebar_text": "#FFFFFF",
    "sidebar_muted": "#7EB8E8",
    "warning": "#FF8C00",
    "warning_bg": "#FFF3CD",
    "success": "#3A8C3A",
    "success_bg": "#D4EDDA",
    "error": "#C0392B",
    "error_bg": "#FDECEA",
}

DARK_THEME = {
    # Wii/WiiU dark palette (WiiU GamePad-inspired deep navy)
    "page_bg": "#000D2A",
    "page_bg_alt": "#001240",
    "stage_bg": "rgba(0, 18, 60, 0.88)",
    "stage_bg_alt": "rgba(0, 30, 80, 0.94)",
    "stage_border": "rgba(77, 179, 255, 0.14)",
    "stage_inner_border": "rgba(77, 179, 255, 0.12)",
    "stage_glow_a": "rgba(0, 63, 138, 0.52)",
    "stage_glow_b": "rgba(0, 154, 199, 0.20)",
    "pattern_line": "rgba(77, 179, 255, 0.07)",
    "card_bg": "rgba(0, 20, 58, 0.80)",
    "card_bg_alt": "rgba(0, 28, 72, 0.62)",
    "glass_bg": "rgba(0, 15, 46, 0.72)",
    "glass_bg_strong": "rgba(0, 22, 62, 0.90)",
    "glass_border": "rgba(77, 179, 255, 0.16)",
    "glass_shadow": "rgba(0, 0, 20, 0.42)",
    "glass_shadow_strong": "rgba(0, 0, 20, 0.65)",
    "hero_from": "rgba(0, 102, 204, 0.96)",
    "hero_via": "rgba(0, 63, 138, 0.98)",
    "hero_to": "rgba(0, 15, 46, 1.0)",
    "hero_highlight": "rgba(255, 255, 255, 0.12)",
    "text": "#EEF4FF",
    "text_soft": "#B8D4F8",
    "text_muted": "#7EB8E8",
    "border": "rgba(77, 179, 255, 0.18)",
    "accent": "#4DB3FF",
    "accent_hover": "#5BC8F5",
    "accent_soft": "rgba(77, 179, 255, 0.18)",
    "sidebar_bg": "#000D2A",
    "sidebar_button": "rgba(255, 255, 255, 0.07)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.14)",
    "sidebar_text": "#EEF4FF",
    "sidebar_muted": "#7EB8E8",
    "warning": "#FF8C00",
    "warning_bg": "rgba(255, 140, 0, 0.16)",
    "success": "#5CB85C",
    "success_bg": "rgba(92, 184, 92, 0.16)",
    "error": "#D9534F",
    "error_bg": "rgba(217, 83, 79, 0.16)",
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
