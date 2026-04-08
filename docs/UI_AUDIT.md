# UI Architecture Audit (RepRight)

## Scope
Audited Streamlit UI code, entrypoint, rendering flow, state lifecycle, and UI/business-logic boundary in the `ui/` layer.

---

## 1) Current UI architecture map (before refactor)

### Entrypoints
- `ui/streamlit_app.py`
  - Single Streamlit entrypoint.
  - Contains **page config**, **session-state init**, **sidebar rendering**, **analysis execution**, **result rendering**, **chat rendering**, **chat persistence**, and **thread loading/saving**.

### Rendering flow (before)
1. `st.set_page_config(...)`
2. Session keys initialized inline.
3. Chat/thread bootstrap inline.
4. Sidebar chat list/actions rendered inline.
5. Left column renders:
   - Exercise select
   - Load input
   - Video upload
   - Analyze button
   - Overlay preview
6. Right column renders:
   - Quality score heading
   - Metrics row
   - Fault expander
   - Download analysis JSON
   - Chat history + follow-up input

### Business/UI mixing hotspots (before)
- Pipeline execution (`RepRightAnalyzer`, payload building, coach call) mixed into page file.
- Chat persistence (JSON IO and thread metadata building) mixed into page file.
- View formatting logic (quality score fallback and color mapping) mixed into page file.
- Artifact path resolution and summary extraction mixed into page file.

---

## 2) File-by-file responsibility map (before)

### `ui/streamlit_app.py`
Everything (high coupling):
- UI orchestration
- Reusable-ish helpers
- Session state init/mutation
- Persistence IO
- Analysis/coaching calls
- Presentation formatting

Consequence: difficult to inspect/edit without scrolling entire file and understanding unrelated concerns.

---

## 3) Repeated patterns & discoverability issues (before)

### Repeated layout/patterns
- Repeated `isinstance(..., dict)` safety checks.
- Repeated fallback extraction patterns for analysis fields.
- Repeated direct `st.session_state` mutation blocks.
- Chat history append pattern duplicated between analyze and follow-up paths.

### Repeated strings/copy
- UI labels/headings/captions hard-coded across the file:
  - button labels
  - section headings
  - warnings
  - expander copy
  - chat placeholders
  - progress text

### Hard-to-edit layout code
- Section order encoded directly via imperative rendering sequence.
- No layout manifest for enabled/disabled sections.
- Left/right column sections not declared centrally.

### Styling hacks / ad hoc bits
- Inline HTML for quality score color rendering.
- Color literals hardcoded in score function.
- No token registry for semantic statuses.

### Session state clarity issues
- Keys initialized in one loop, but mutated in many unrelated locations.
- No explicit grouping between chat state vs analysis state vs UI-transient state.
- Exercise locking behavior intertwined with render code.

---

## 4) Severity-ranked pain points (before)

## Critical
1. **Single-file architecture with mixed concerns** (UI, IO, business calls, formatting).
2. **No centralized copy/tokens/layout configuration** (high edit friction).
3. **Session state mutation spread across unrelated logic blocks**.

## High
4. **No config-driven section composition** (reordering/extending requires imperative edits).
5. **No reusable panel primitives** (future cards/sections lead to duplication).

## Medium
6. **Presentation mapping logic embedded near render calls**.
7. **Thread/chat persistence tightly coupled to UI file**.

## Low
8. Inline styling not abstracted into semantic tokens.

---

## 5) Easy wins vs structural issues

### Easy wins
- Centralize labels/headings/captions into a single text registry.
- Centralize quality/status colors into semantic tokens.
- Extract sidebar, input panel, results panel, and chat panel renderers.

### Structural issues
- Introduce composition manifest for section order/enablement.
- Introduce dedicated session-state module with explicit defaults/groups.
- Move thread persistence into dedicated storage helper.
- Move pipeline execution and follow-up calls into service layer.
- Move analysis-to-UI transforms into view-model helpers.

---

## 6) Exact refactor recommendations

1. Create `ui/config/tokens.py` with:
   - copy registry
   - semantic colors/statuses
   - empty states
   - section feature flags
2. Create `ui/config/layout.py` with ordered left/right section manifests.
3. Create reusable primitives in `ui/components/primitives.py`.
4. Create panel renderers in `ui/components/panels.py`.
5. Create state module `ui/state.py`:
   - defaults
   - grouped reset helpers
   - history append helper
6. Create chat persistence module `ui/chat_store.py`.
7. Create view-model module `ui/view_models.py` for UI shaping/mapping.
8. Create service module `ui/services.py` for analysis/coaching orchestration.
9. Keep `ui/streamlit_app.py` as orchestration-only glue.

---

## 7) “Where to edit what” map (post-refactor target)

- Change wording globally: `ui/config/tokens.py` (`TEXT`, `EMPTY_STATES`).
- Change section order: `ui/config/layout.py` (`LEFT_SECTIONS`, `RIGHT_SECTIONS`).
- Enable/disable sections: `ui/config/tokens.py` (`SECTION_FLAGS`).
- Change quality/status colors: `ui/config/tokens.py` (`QUALITY_ZONES`).
- Change result card layout/metric row behavior: `ui/components/panels.py` (`render_summary_metrics`).
- Change chat panel rendering: `ui/components/panels.py` (`render_chat_panel`).
- Add new metrics card: implement in `ui/components/panels.py`, wire section in `ui/config/layout.py`.
- Add sidebar control: `ui/streamlit_app.py::render_sidebar` (or extract dedicated sidebar panel if it grows).
- Change upload flow UI: `ui/components/panels.py::render_analysis_controls`.
- Change view-model mapping/formatting rules: `ui/view_models.py`.

---

## 8) Backward-safety notes
- Core analyzer/coaching backend contracts remain unchanged.
- Refactor focuses on UI boundaries and render architecture.
- Functional behavior preserved for upload → analyze → metrics/chat flow and thread persistence.
