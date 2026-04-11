from __future__ import annotations

EXERCISES = ["bench", "deadlift", "squat", "curl"]

EXERCISE_ICONS = {
    "bench":    "🏋️",
    "deadlift": "⬆️",
    "squat":    "🦵",
    "curl":     "💪",
}

PAGE = {
    "title":   "RepRight",
    "layout":  "wide",
    "columns": [1.5, 1],
}

THEME = {
    "page_bg": "#eef2f7",
    "card_bg": "#ffffff",
    "card_bg_alt": "#f8fafc",
    "text": "#0f172a",
    "text_soft": "#334155",
    "text_muted": "#64748b",
    "border": "#d7e0ea",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_soft": "#dbeafe",
    "sidebar_bg": "#16233b",
    "sidebar_button": "#22314d",
    "sidebar_button_hover": "#2c4367",
    "sidebar_text": "#e2e8f0",
    "sidebar_muted": "#9fb1c8",
    "warning": "#b45309",
    "warning_bg": "#fef3c7",
    "success": "#15803d",
    "success_bg": "#dcfce7",
    "error": "#b91c1c",
    "error_bg": "#fee2e2",
}

TEXT = {
    "sidebar": {
        "new_chat":          "+ New Session",
        "new_chat_help":     "Start a fresh draft without saving an empty session.",
        "clear_chat":        "Clear messages",
        "clear_chat_help":   "Remove chat messages and coaching, but keep the current analysis.",
        "sessions_header":   "Sessions",
        "recent_header":     "Recent Sessions",
    },
    "inputs": {
        "exercise":          "Exercise",
        "exercise_locked":   "Exercise is locked to this analyzed set. Start a new session to analyze a different lift.",
        "load":              "Load (KG)",
        "upload":            "Upload Set Video",
        "coach_note":        "Note to Coach (Optional)",
        "analyze":           "Analyze set →",
        "upload_warning":    "Please upload a video before analyzing.",
        "busy_help":         "Analysis is running. Controls will unlock when it finishes.",
    },
    "results": {
        "quality_title": "Lift Quality",
        "reps":          "Reps",
        "avg_rom":       "Avg ROM",
        "low_confidence":"Low conf. reps",
        "why_score":     "Form Breakdown",
        "no_faults":     "No recurring faults detected — clean set.",
        "download_json": "⬇  Export analysis JSON",
    },
    "chat": {
        "follow_up":          "Ask your coach anything...",
        "follow_up_disabled": "Run an analysis to ask follow-up questions.",
    },
    "states": {
        "empty_title":   "No analysis results yet.",
        "empty_body":    "Upload a video of a set and get feedback on your form, metrics, and potential improvements.",
        "empty_results": "Upload a video and run an analysis to see your form score, detailed metrics, and AI coaching in this pane.",
    },
    "progress": {
        "tracking": "Tracking pose…",
        "context":  "Building coach context…",
        "coach":    "Generating coaching response…",
        "done":     "Done.",
    },
    "errors": {
        "analysis_failed": "Analysis failed. Please try again with another upload or review the error details below.",
        "followup_failed": "Coach follow-up failed. Please try again in a moment.",
        "details_prefix":  "Details:",
    },
    "coaching_panel": {
        "title":       "Coaching Overview",
        "subtitle":    "Upload a video and run an analysis\nto see your form score, detailed\nmetrics, and AI coaching in this pane.",
        "how_title":   "How it Works",
        "tip":         "Tip: Side views work best for analyzing most exercises.",
        "steps": [
            ("📷", "Camera Pose Estimation", "AI analyzes your movement."),
            ("✅", "Form Assessment",         "Get rep breakdown and metrics."),
            ("💬", "Coaching Feedback",       "Receive personalized AI guidance."),
        ],
    },
    "main_title": "Analyze Your Set",
    "recent_sessions_title": "Recent Sessions",
}

QUALITY_ZONES = {
    "none":   {"color": "#64748b", "label": "No data",    "bg": "#f1f5f9", "ring": "#cbd5e1"},
    "green":  {"color": "#16a34a", "label": "Good form",  "bg": "#dcfce7", "ring": "#86efac"},
    "yellow": {"color": "#d97706", "label": "Needs work", "bg": "#fef3c7", "ring": "#fcd34d"},
    "red":    {"color": "#dc2626", "label": "Poor form",  "bg": "#fee2e2", "ring": "#fca5a5"},
}

FAULT_SEVERITY_COLORS = {
    "critical": ("#dc2626", "#fee2e2"),
    "high":     ("#ea580c", "#ffedd5"),
    "medium":   ("#d97706", "#fef3c7"),
    "warning":  ("#d97706", "#fef3c7"),
    "info":     ("#64748b", "#f1f5f9"),
}

EMPTY_STATES = {
    "video": "No overlay yet. Run an analysis to generate a pose-annotated replay.",
    "chat":  "Ask about your form after running an analysis.",
}

SECTION_FLAGS = {
    "left_input_panel":      True,
    "left_overlay_panel":    True,
    "right_results_header":  True,
    "right_results_metrics": True,
    "right_faults":          True,
    "right_artifacts":       True,
    "right_chat":            True,
}
