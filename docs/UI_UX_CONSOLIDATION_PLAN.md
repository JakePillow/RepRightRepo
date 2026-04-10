# UI/UX Consolidation Plan (High-level + Low-level)

## Goal
Unify legacy and new UI behaviors into one coherent experience while eliminating duplicate progress/form appraisals and enforcing durable text contrast/accessibility.

## High-level architecture plan

### 1) Single source of truth for session + analysis identity
- Move all thread identity fields behind a canonical model:
  - `thread_id`, `exercise_canonical`, `analysis_json`, `schema_version`, `artifact_status`
- Never derive canonical exercise from display labels or thread-id suffixes after analysis completes.
- Keep a `summary_snapshot` for resilient old-thread rendering when artifacts are unavailable.

### 2) One rendering pathway for coaching output
- Split “analysis overview” from “conversation thread”:
  - Overview card: latest analysis appraisal (single location)
  - Chat thread: only user follow-ups and follow-up responses
- This removes duplicated appraisal blocks and keeps conversation history meaningful.

### 3) Unified progress UX
- Consolidate to one status line + one progress bar.
- Ensure each stage has a single visible message and no duplicated text.

### 4) Accessibility baseline by default
- Apply strong contrast tokens globally for body text, captions, chat content, and sidebar text.
- Keep semantic badge color, but never rely on color alone for meaning (show label + score).

### 5) Consolidation of legacy/new sections
- Keep all page section registration in one layout manifest.
- Migrate any legacy widgets to panel renderers and remove parallel UI paths.

---

## Low-level implementation plan

## Phase A — reliability + duplication cleanup (immediate)
1. Add dedicated `render_coaching_overview()` panel and show the latest response once.
2. Mark initial analysis assistant message (`analysis_response_ts`) and hide that one from chat timeline rendering.
3. Replace text-in-progress-bar pattern with explicit caption status + plain progress bar.
4. Inject accessibility CSS for text contrast across app/sidebar/chat.

## Phase B — thread model hardening
5. Extend thread JSON schema with:
   - `analysis_identity`
   - `summary_snapshot`
   - `artifact_status`
6. Add legacy loader adapter:
   - Detect old thread shape
   - Populate missing identity/snapshot fields
   - Persist upgraded thread on next save
7. Add UI warning states for `snapshot_only` and `missing` artifacts.

## Phase C — full legacy/new convergence
8. Inventory all legacy UI fragments and map each to current `panels.py` sections.
9. Remove duplicate rendering logic and dead components after parity checks.
10. Add visual regression checklist for analyze flow, chat flow, old-thread load flow.

---

## UX acceptance criteria
- No duplicate progress text appears during analysis.
- No duplicate full appraisal block appears in both overview and chat timeline.
- Text remains readable in light/dim browser themes (minimum contrast target WCAG AA for normal text).
- Loading an old chat always shows either full analysis or explicit snapshot/missing state (never silent degradation).
- Exercise shown in UI matches canonical analysis exercise for every loaded thread.

---

## Rollout sequence (recommended)
1. Ship Phase A immediately (low risk, visible UX improvement).
2. Ship Phase B behind lightweight thread migration guard.
3. Ship Phase C after one release cycle of telemetry and user validation.
