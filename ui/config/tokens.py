from __future__ import annotations

EXERCISES = ["bench", "deadlift", "squat", "curl"]

EXERCISE_ICONS = {
    "bench": "\U0001F3CB\uFE0F",
    "deadlift": "\u2191",
    "squat": "\u25BE",
    "curl": "\U0001F4AA",
}

PAGE = {
    "title": "RepRight",
    "layout": "wide",
    "columns": [1.5, 1],
}

THEME = {
    "page_bg": "#eef3f8",
    "page_bg_alt": "#f8fbfd",
    "stage_bg": "rgba(255, 255, 255, 0.82)",
    "stage_bg_alt": "rgba(244, 248, 252, 0.94)",
    "stage_border": "rgba(255, 255, 255, 0.82)",
    "stage_inner_border": "rgba(148, 163, 184, 0.22)",
    "stage_glow_a": "rgba(255, 255, 255, 0.94)",
    "stage_glow_b": "rgba(96, 165, 250, 0.16)",
    "pattern_line": "rgba(15, 23, 42, 0.04)",
    "card_bg": "rgba(255, 255, 255, 0.92)",
    "card_bg_alt": "rgba(244, 247, 251, 0.94)",
    "glass_bg": "rgba(255, 255, 255, 0.74)",
    "glass_bg_strong": "rgba(255, 255, 255, 0.94)",
    "glass_border": "rgba(148, 163, 184, 0.18)",
    "glass_shadow": "rgba(15, 23, 42, 0.08)",
    "glass_shadow_strong": "rgba(15, 23, 42, 0.14)",
    "hero_from": "rgba(15, 23, 42, 0.98)",
    "hero_via": "rgba(30, 64, 175, 0.96)",
    "hero_to": "rgba(14, 165, 233, 0.94)",
    "hero_highlight": "rgba(255, 255, 255, 0.18)",
    "text": "#0f172a",
    "text_soft": "#1e293b",
    "text_muted": "#64748b",
    "border": "rgba(148, 163, 184, 0.24)",
    "accent": "#2563eb",
    "accent_hover": "#1d4ed8",
    "accent_soft": "rgba(37, 99, 235, 0.12)",
    "sidebar_bg": "#0f172a",
    "sidebar_button": "rgba(255, 255, 255, 0.06)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.10)",
    "sidebar_text": "#e2e8f0",
    "sidebar_muted": "#94a3b8",
    "warning": "#d97706",
    "warning_bg": "rgba(245, 158, 11, 0.12)",
    "success": "#15803d",
    "success_bg": "rgba(34, 197, 94, 0.12)",
    "error": "#dc2626",
    "error_bg": "rgba(239, 68, 68, 0.12)",
}

DARK_THEME = {
    "page_bg": "#07111f",
    "page_bg_alt": "#0d1728",
    "stage_bg": "rgba(12, 22, 36, 0.82)",
    "stage_bg_alt": "rgba(15, 23, 42, 0.94)",
    "stage_border": "rgba(148, 163, 184, 0.08)",
    "stage_inner_border": "rgba(148, 163, 184, 0.14)",
    "stage_glow_a": "rgba(30, 41, 59, 0.44)",
    "stage_glow_b": "rgba(59, 130, 246, 0.16)",
    "pattern_line": "rgba(148, 163, 184, 0.06)",
    "card_bg": "rgba(15, 23, 42, 0.84)",
    "card_bg_alt": "rgba(17, 24, 39, 0.92)",
    "glass_bg": "rgba(15, 23, 42, 0.68)",
    "glass_bg_strong": "rgba(17, 24, 39, 0.92)",
    "glass_border": "rgba(148, 163, 184, 0.14)",
    "glass_shadow": "rgba(2, 6, 23, 0.32)",
    "glass_shadow_strong": "rgba(2, 6, 23, 0.5)",
    "hero_from": "rgba(15, 23, 42, 0.98)",
    "hero_via": "rgba(30, 64, 175, 0.96)",
    "hero_to": "rgba(2, 132, 199, 0.94)",
    "hero_highlight": "rgba(255, 255, 255, 0.08)",
    "text": "#e5eefb",
    "text_soft": "#c8d4e7",
    "text_muted": "#8ea1bb",
    "border": "rgba(148, 163, 184, 0.16)",
    "accent": "#60a5fa",
    "accent_hover": "#93c5fd",
    "accent_soft": "rgba(96, 165, 250, 0.18)",
    "sidebar_bg": "#020817",
    "sidebar_button": "rgba(255, 255, 255, 0.06)",
    "sidebar_button_hover": "rgba(255, 255, 255, 0.12)",
    "sidebar_text": "#e2e8f0",
    "sidebar_muted": "#8ea1bb",
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
        "exercise_locked": "Exercise is locked to this analysed set. Start a new session to analyse a different lift.",
        "load": "Load (KG)",
        "upload": "Upload Set Video",
        "coach_note": "Note to Coach (Optional)",
        "analyze": "Analyse set ->",
        "upload_warning": "Please upload a video before analysing.",
        "busy_help": "Analysis is running. Controls will unlock when it finishes.",
    },
    "results": {
        "quality_title": "Lift Quality",
        "reps": "Reps",
        "avg_rom": "Avg ROM",
        "low_confidence": "Low confidence reps",
        "why_score": "Form Breakdown",
        "no_faults": "No recurring faults detected - clean set.",
        "download_json": "Export analysis JSON",
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
        "tracking": "Tracking pose...",
        "context": "Building coach context...",
        "coach": "Generating coaching response...",
        "done": "Done.",
    },
    "errors": {
        "analysis_failed": "Analysis failed. Please try again with another upload or review the error details below.",
        "followup_failed": "Follow-up coaching failed. Please try sending your question again.",
        "details_prefix": "Details:",
    },
    "coaching_panel": {
        "title": "Coaching Overview",
        "subtitle": "Upload a video and run an analysis to see your form score, detailed metrics, and AI coaching in this pane.",
        "how_title": "How it Works",
        "view_all": "View all",
        "tip": "Tip: Side views work best for analysing most exercises.",
        "steps": [
            ("\U0001F4F9", "Capture the set", "Upload a clean side-view clip for the strongest replay and fault analysis."),
            ("\U0001F4CA", "Review the replay", "Inspect the overlay, compare against your previous set, and spot the main changes."),
            ("\U0001F4AC", "Coach the next step", "Use the chat to ask for cues, rep fixes, or what to change on the next set."),
        ],
    },
    "main_title": "RepRight Coach",
    "main_subtitle": "Upload a set, review the overlay, and keep follow-up coaching in one place.",
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
