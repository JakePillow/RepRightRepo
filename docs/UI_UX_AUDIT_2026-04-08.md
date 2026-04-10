# RepRight UI + UX Audit (April 8, 2026)

## Audit scope
This audit focuses on the current Streamlit UI behavior for:
- Session/thread storage and retrieval
- Canonical analysis truth alignment
- Discoverability and trust in old chats
- Interaction flow (upload → analyze → review → follow-up)
- Information architecture and microcopy clarity

Code reviewed: `ui/streamlit_app.py`, `ui/chat_store.py`, `ui/components/panels.py`, `ui/view_models.py`, `ui/services.py`, and UI token/layout config.

---

## Executive summary
The app has a clean modular structure and a straightforward happy path, but there is a **high-severity data integrity UX gap** in chat/thread rehydration:

1. Thread loading can silently degrade to partial data when the linked analysis JSON no longer exists.
2. Exercise identity in thread metadata can drift from analysis truth because it is derived from mutable UI state/fallbacks.
3. Old chats have no explicit “data unavailable” status, so users perceive missing historical details as data loss/buggy behavior.

This directly matches the reported issue: chat sessions and loaded context can diverge from canonical exercise truth, and old chats appear to “lose” information.

---

## What works well right now

### 1) Strong UI architecture separation
- Orchestration, storage, state, service calls, and rendering are split into dedicated files.
- Section layout is config-driven (`LEFT_SECTIONS`, `RIGHT_SECTIONS`) and feature flags exist.

### 2) Good baseline interaction model
- New chat creation and chat switching are simple from the sidebar.
- Upload + analyze flow has progress feedback and a clear empty state.
- Follow-up chat is conditioned on having analysis, reducing invalid requests.

### 3) Useful result affordances
- Quality badge + compact metrics row + “Why this score?” expander aid quick interpretation.
- JSON download supports reproducibility and external debugging.

---

## Critical issues (UI/UX + data model mismatch)

## C1. Canonical exercise truth can drift in persisted threads (High)
**Observed behavior**
- `save_thread()` derives `exercise` using fallback sources (`analysis.exercise`, `exercise_choice`, or parsing from thread ID).
- This means thread metadata can be saved using mutable UI state or string heuristics when analysis is missing/incomplete.

**User impact**
- Sidebar titles and restored exercise selection can disagree with what the original set actually was.
- Over time, this creates trust issues (“this was a deadlift set, why does thread show bench?”).

**Root cause**
- Thread metadata is treated as canonical instead of being anchored to immutable analysis identity once the first successful analysis exists.

**Fix recommendation**
- Introduce immutable per-thread `analysis_identity` fields after first analysis success:
  - `exercise_canonical`
  - `analysis_schema_version`
  - `analysis_id` (or stable hash/path key)
- On subsequent saves, never overwrite canonical fields from UI state.

---

## C2. Old chats silently rehydrate into partial synthetic analysis objects (High)
**Observed behavior**
- During `load_thread()`, if `analysis_json` is missing/unreadable, app creates a minimal fallback analysis object with only exercise/paths.
- No visible warning is shown to users.

**User impact**
- Historical metrics/faults/context disappear without explanation.
- Users interpret this as random deletion/corruption.

**Root cause**
- Missing artifact handling is silent and non-diagnostic.
- No durable summary snapshot is stored in thread file.

**Fix recommendation**
- Persist a `summary_snapshot` at save time containing minimally required read-only fields:
  - `quality_score`, `n_reps`, `avg_rom`, `top_faults`, `timestamp`, `exercise_canonical`
- On load, if analysis artifact is unavailable:
  - show explicit warning badge: “Full analysis artifact unavailable; showing saved snapshot.”
  - render snapshot values instead of empty/N/A.

---

## C3. Chat history is persisted, but analysis provenance is not user-visible (Medium-High)
**Observed behavior**
- The UI shows chat content but not the analysis version/provenance the chat was based on.

**User impact**
- Users cannot tell whether follow-up advice references current analysis, stale analysis, or fallback data.

**Fix recommendation**
- Add a compact provenance line in results/chat header:
  - exercise, analyzed_at timestamp, schema version, artifact availability state.

---

## Important UX issues

## U1. Exercise selector lock behavior is correct technically but opaque (Medium)
After analysis, exercise control becomes disabled, but there is no explanation text.

**Improve**
- Add helper text: “Exercise is locked to this thread’s analyzed set. Start a new chat to analyze a different exercise.”

## U2. Sidebar threads lack context density (Medium)
Thread buttons show title only; no metadata for status or artifact health.

**Improve**
- Show secondary metadata in sidebar list:
  - exercise tag
  - last updated
  - badge for `artifact present / snapshot only / missing`

## U3. “Clear current chat” can feel destructive/ambiguous (Medium)
Currently clears history and response/payload but does not obviously communicate what remains.

**Improve**
- Rename to “Clear messages (keep analysis)” or add confirm/help text.

## U4. Missing error states for failed analyze/follow-up paths (Medium)
Service calls do not wrap failures into user-friendly diagnostics.

**Improve**
- Show structured failure banner + retry action + small error details expander.

---

## Suggested storage contract revision (practical)

Thread schema additions:
- `thread_id`
- `created_at`, `updated_at`
- `title`
- `analysis_identity`:
  - `exercise_canonical`
  - `analysis_json`
  - `run_dir`
  - `schema_version`
  - `analyzed_at`
- `summary_snapshot` (denormalized summary for durable old-chat rendering)
- `history`
- `artifact_status` (`full`, `snapshot_only`, `missing`)

Behavior rules:
1. First successful analysis writes immutable `analysis_identity`.
2. Later saves cannot mutate `exercise_canonical`.
3. Load path always computes and displays `artifact_status`.
4. UI renders best-available data in this priority:
   - full analysis artifact
   - snapshot
   - explicit empty state with remediation message

---

## Prioritized implementation plan

### Phase 1 (fast, high-value)
1. Add explicit missing-artifact warning in `load_thread()` path.
2. Save `summary_snapshot` in thread JSON.
3. Display artifact status + provenance in UI header.

### Phase 2 (data integrity hardening)
4. Introduce immutable canonical exercise in thread schema.
5. Stop deriving exercise from thread-id fallback for persisted metadata.
6. Add migration adapter for legacy thread files.

### Phase 3 (UX polish)
7. Improve sidebar thread cards with metadata badges.
8. Clarify button copy around chat clearing and exercise lock.
9. Add empty/error states with next-step guidance.

---

## Success metrics to track
- % of loaded threads with artifact_status != `full`
- % of sessions where displayed exercise != canonical exercise (should be 0)
- User-reported “lost old chat info” incidents per week
- Follow-up message success rate after loading old thread

---

## Bottom line
The core UI architecture is solid and extensible, but thread persistence/rehydration currently under-specifies data durability and canonical identity. Tightening the storage contract and surfacing artifact status in the UI will eliminate most trust-breaking behavior around old chats and exercise mismatch.
