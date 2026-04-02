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
    "columns": [1.05, 0.95],
}

TEXT = {
    "sidebar": {
        "new_chat":     "+ New session",
        "clear_chat":   "Clear chat",
        "chats_header": "### Sessions",
    },
    "inputs": {
        "exercise":       "Exercise",
        "load":           "Load (kg)",
        "upload":         "Upload set video",
        "coach_note":     "Note to coach (optional)",
        "analyze":        "Analyze set →",
        "upload_warning": "Please upload a video before analyzing.",
    },
    "results": {
        "quality_title": "Lift Quality",
        "reps":          "Reps",
        "avg_rom":       "Avg ROM",
        "low_confidence":"Low conf. reps",
        "why_score":     "Form breakdown",
        "no_faults":     "No recurring faults detected — clean set.",
        "download_json": "⬇  Export analysis JSON",
    },
    "chat": {
        "follow_up": "Ask your coach anything...",
    },
    "states": {
        "empty_results": "Upload a video and run an analysis to see your form score, metrics, and AI coaching.",
    },
    "progress": {
        "tracking": "Tracking pose…",
        "context":  "Building coach context…",
        "coach":    "Generating coaching response…",
        "done":     "Done.",
    },
}

QUALITY_ZONES = {
    "none":   {"color": "#6b7280", "label": "No data",    "bg": "#1f2937", "ring": "#374151"},
    "green":  {"color": "#10b981", "label": "Good form",  "bg": "#064e3b", "ring": "#059669"},
    "yellow": {"color": "#f59e0b", "label": "Needs work", "bg": "#451a03", "ring": "#d97706"},
    "red":    {"color": "#ef4444", "label": "Poor form",  "bg": "#450a0a", "ring": "#dc2626"},
}

FAULT_SEVERITY_COLORS = {
    "critical": ("#ef4444", "#450a0a"),
    "high":     ("#f97316", "#431407"),
    "medium":   ("#f59e0b", "#451a03"),
    "warning":  ("#f59e0b", "#451a03"),
    "info":     ("#6b7280", "#1f2937"),
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
