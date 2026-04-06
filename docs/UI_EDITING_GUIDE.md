# RepRight UI Editing Guide (High-Level, Fast Edits)

This guide is for quick, low-friction UI changes.

---

## TL;DR: Start here first

1. **Text/copy changes** → `ui/config/tokens.py` (`TEXT`, `EMPTY_STATES`)
2. **Section order / enablement** → `ui/config/layout.py` + `ui/config/tokens.py` (`SECTION_FLAGS`)
3. **Section rendering details** → `ui/components/panels.py`
4. **Visual semantics (quality colors/zones)** → `ui/config/tokens.py` (`QUALITY_ZONES`)
5. **Data-to-UI mapping** → `ui/view_models.py`
6. **Pipeline behavior wiring (still UI-facing)** → `ui/services.py`

---

## Where do I change copy/text globally?

Edit:
- `ui/config/tokens.py`
  - `TEXT` for labels/buttons/headings/placeholders/progress strings
  - `EMPTY_STATES` for reusable “nothing yet” messages

Use this when renaming:
- button labels
- section titles
- metric labels
- warnings/helper text
- chat prompt text

---

## Where do I change colors / spacing / card look?

Edit:
- `ui/config/tokens.py`
  - `QUALITY_ZONES` for score color semantics
- `ui/components/primitives.py`
  - `render_quality_badge(...)` for shared score badge presentation

If you need broader style primitives, add new token groups (e.g., `SPACING`, `CARD_STYLE`) in `tokens.py` and consume them from panels/primitives.

---

## Where do I change page structure?

Edit:
- `ui/config/layout.py`
  - `LEFT_SECTIONS`
  - `RIGHT_SECTIONS`

These lists define section order and the renderer to call.

---

## Where do I add a new section?

1. Implement a new renderer in `ui/components/panels.py`.
2. Register it in `RENDERERS` inside `ui/streamlit_app.py`.
3. Add a section entry in `ui/config/layout.py`.
4. Add a feature flag in `ui/config/tokens.py::SECTION_FLAGS`.

---

## Where do I add a new reusable card?

1. If broadly reusable, create a small primitive in `ui/components/primitives.py`.
2. Consume it in one or more panel renderers in `ui/components/panels.py`.
3. If card labels/copy are user-facing, add strings to `ui/config/tokens.py`.

---

## Where do I add a new result metric?

Option A (simple):
- Edit `ui/view_models.py::summary_metrics(...)` to add metric data.

Option B (layout-specific):
- Edit `ui/components/panels.py::render_summary_metrics(...)` for new card/column layout.

---

## Where do I change upload flow UI?

Edit:
- `ui/components/panels.py::render_analysis_controls(...)`

This controls:
- exercise selector
- load input
- uploader
- optional note
- analyze trigger behavior

---

## Where do I change chat UI?

Edit:
- `ui/components/panels.py::render_chat_panel(...)`

For data persistence/history behavior:
- `ui/chat_store.py`

For follow-up coach call wiring:
- `ui/services.py::run_followup_coaching(...)`

---

## Where do I reorder panels?

Edit only:
- `ui/config/layout.py`

No need to rewrite main page logic.

---

## Where do I enable/disable sections?

Edit only:
- `ui/config/tokens.py::SECTION_FLAGS`

Set a section flag to `False` to hide it without deleting code.

---

## Session state quick map

Defined centrally in:
- `ui/state.py::SESSION_DEFAULTS`

Main groups:
- chat state: `history`
- analysis state: `last_analysis`, `last_payload`, `last_response`
- identity/thread state: `thread_id`, `thread_created_at`, `thread_title`
- input UI state: `exercise_choice`, `ui_load_kg`

Reset helpers:
- `reset_group("chat")`
- `reset_group("analysis")`

---

## Typical “I’m tired” edit recipes

### Rename “Analyze set” button
- Edit `TEXT["inputs"]["analyze"]` in `ui/config/tokens.py`.

### Hide download JSON button
- Set `SECTION_FLAGS["right_artifacts"] = False` in `ui/config/tokens.py`.

### Move chat above metrics
- Reorder `RIGHT_SECTIONS` in `ui/config/layout.py`.

### Add a new “Tempo” metrics block
1. Add view-model function/data in `ui/view_models.py`.
2. Add `render_tempo_panel()` in `ui/components/panels.py`.
3. Register renderer in `ui/streamlit_app.py`.
4. Add section in `ui/config/layout.py`.
5. Add section flag in `ui/config/tokens.py`.

---

## Design intent

- Keep `streamlit_app.py` orchestration-only.
- Keep business/analysis contracts unchanged.
- Keep UI editing high-level via config + panel modules.
- Keep future thesis iteration fast and understandable.
