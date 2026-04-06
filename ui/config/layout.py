from __future__ import annotations

LEFT_SECTIONS = [
    {"id": "left_input_panel", "renderer": "render_analysis_controls", "enabled_flag": "left_input_panel"},
    {"id": "left_overlay_panel", "renderer": "render_overlay_panel", "enabled_flag": "left_overlay_panel"},
]

RIGHT_SECTIONS = [
    {"id": "right_results_header", "renderer": "render_quality_header", "enabled_flag": "right_results_header"},
    {"id": "right_results_metrics", "renderer": "render_summary_metrics", "enabled_flag": "right_results_metrics"},
    {"id": "right_faults", "renderer": "render_faults_panel", "enabled_flag": "right_faults"},
    {"id": "right_artifacts", "renderer": "render_artifacts_panel", "enabled_flag": "right_artifacts"},
    {"id": "right_chat", "renderer": "render_chat_panel", "enabled_flag": "right_chat"},
]
