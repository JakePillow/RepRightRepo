# UI Refactor Summary

## What changed
- Split monolithic `ui/streamlit_app.py` responsibilities into focused modules.
- Added centralized UI tokens/copy and section flags.
- Added config-driven page composition for left/right panel ordering.
- Added reusable panel and primitive renderers.
- Added a lightweight view-model layer for analysis-to-UI mapping.
- Added centralized session state defaults/resets.
- Added dedicated chat thread persistence module.
- Kept analyzer/coaching backend flow intact.

## New file structure
- `ui/streamlit_app.py` — orchestration only
- `ui/config/tokens.py` — text, semantic colors, flags, constants
- `ui/config/layout.py` — section order and renderer mapping declarations
- `ui/components/primitives.py` — reusable UI primitives
- `ui/components/panels.py` — concrete UI sections/panels
- `ui/view_models.py` — formatting/mapping helpers for results
- `ui/services.py` — analysis/follow-up call orchestration
- `ui/state.py` — session-state schema and reset helpers
- `ui/chat_store.py` — chat thread list/load/save
- `docs/UI_AUDIT.md` — architecture audit
- `docs/UI_EDITING_GUIDE.md` — high-level editing playbook

## Biggest maintainability wins
1. One obvious source for UI text and semantic display tokens.
2. One obvious source for panel order and enable/disable toggles.
3. Streamlit app page now reads as orchestration logic.
4. Session state keys and reset behavior are centralized.
5. Rendering and data-shaping concerns are isolated and easier to test/reason about.

## 10 most common UI edits (where to do them)
1. Rename labels/buttons → `ui/config/tokens.py`
2. Change empty-state copy → `ui/config/tokens.py`
3. Reorder right-column panels → `ui/config/layout.py`
4. Reorder left-column panels → `ui/config/layout.py`
5. Disable a section temporarily → `ui/config/tokens.py::SECTION_FLAGS`
6. Change quality score colors/zones → `ui/config/tokens.py::QUALITY_ZONES`
7. Modify upload/input controls → `ui/components/panels.py::render_analysis_controls`
8. Modify chat rendering/input behavior → `ui/components/panels.py::render_chat_panel`
9. Add new summary metric data formatting → `ui/view_models.py`
10. Add new panel/card → `ui/components/panels.py` + `ui/streamlit_app.py` registry + `ui/config/layout.py`

## Tradeoffs introduced
- More files/modules to navigate initially.
- Slightly more indirection (config + registry + renderer) in exchange for clearer extension points.
- If panel count grows significantly, consider splitting `panels.py` into domain-specific panel modules.
