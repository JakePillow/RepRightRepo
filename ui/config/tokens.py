from __future__ import annotations

EXERCISES = ["bench", "deadlift", "squat", "curl"]

PAGE = {
    "title": "RepRight",
    "layout": "wide",
    "columns": [1.05, 0.95],
}

TEXT = {
    "sidebar": {
        "new_chat": "+ New chat",
        "clear_chat": "Clear current chat",
        "chats_header": "### Chats",
    },
    "inputs": {
        "exercise": "Exercise",
        "load": "Load (kg)",
        "upload": "Upload set video",
        "coach_note": "Optional note to coach",
        "analyze": "Analyze set",
        "upload_warning": "Upload a video first.",
    },
    "results": {
        "quality_title": "Lift Quality",
        "reps": "Reps",
        "avg_rom": "Avg ROM",
        "low_confidence": "Low confidence reps",
        "why_score": "Why this score?",
        "no_faults": "No major recurring faults were detected for this set.",
        "download_json": "Download analysis JSON",
    },
    "chat": {
        "follow_up": "Ask a follow-up...",
    },
    "states": {
        "empty_results": "Run an analysis to see metrics and coaching details.",
    },
    "progress": {
        "tracking": "Tracking pose...",
        "context": "Building coach context...",
        "coach": "Generating coaching response...",
        "done": "Done.",
    },
}

QUALITY_ZONES = {
    "none": {"color": "#8a8f98", "label": "n/a"},
    "green": {"color": "#35d07f", "label": "Green"},
    "yellow": {"color": "#f0c04f", "label": "Yellow"},
    "red": {"color": "#f25f5c", "label": "Red"},
}

EMPTY_STATES = {
    "video": "No overlay available yet. Upload and analyze a set to generate one.",
    "chat": "Ask for form feedback after running analysis.",
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
