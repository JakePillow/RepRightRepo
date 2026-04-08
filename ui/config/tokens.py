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

TEXT = {
    "sidebar": {
        "new_chat":          "+ New Session",
        "clear_chat":        "Clear chat",
        "sessions_header":   "Sessions",
        "recent_header":     "Recent Sessions",
    },
    "inputs": {
        "exercise":       "Exercise",
        "load":           "Load (KG)",
        "upload":         "Upload Set Video",
        "coach_note":     "Note to Coach (Optional)",
        "analyze":        "Analyze set →",
        "upload_warning": "Please upload a video before analyzing.",
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
        "follow_up": "Ask your coach anything...",
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
    "coaching_panel": {
        "title":       "Coaching Overview",
        "subtitle":    "Upload a video and run an analysis\nto see your form score, detailed\nmetrics, and AI coaching in this pane.",
        "how_title":   "How it Works",
        "view_all":    "View all",
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
