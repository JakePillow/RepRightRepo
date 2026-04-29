# RepRight Final Program Audit (March 30, 2026)

## Scope and method
This final audit reviewed repository structure, pipeline/analyzer integration, coach payload assembly, LLM response handling, CLI/evaluation utilities, and the Streamlit demo UX. The goal was to identify removable redundancies, thesis-report explainability upgrades, and low-risk final-demo UI/UX improvements.

---

## 1) Redundancies that can be removed or consolidated

### 1.1 Backup and temporary artifacts in tracked source tree
The repository currently contains backup and temporary files that duplicate active code paths and increase maintenance drag:

- `repright/llm_wrapper.py.bak_20260223_150746`
- `scripts/evaluate.py.bak`
- `scripts/run_cli.py.bak`
- `scripts/make_overlay_from_npz.py.bak_20260218_213118`
- `scripts/make_overlay_from_npz.py.bak_20260218_214451`
- `tools/build_coach_payload.ps1.bak_20260223_193500`
- `_tmp_*.py` and `_tmp_*.ps1` files at repo root
- Multiple archived zip snapshots (`gpt_inspect.zip`, `_gpt_inspect.zip`, etc.)

**Recommendation:** move these into an untracked `archive/` directory or delete after tagging a release. This will reduce review noise and accidental import/run risks.

### 1.2 Analyzer/pipeline signature compatibility fallback complexity
`repright/analyser.py` includes multi-layer `TypeError` fallback logic to call `run_full_pipeline` under several possible signatures. This is useful during migration, but now that architecture is locked, this is unnecessary runtime branching and cognitive overhead.

**Recommendation:** freeze one canonical signature for `run_full_pipeline(...)` and remove fallback branches after one final compatibility checkpoint.

### 1.3 Duplicate analysis path aliases
Across components, equivalent artifact pointers are represented as:
- `analysis_json`
- `metrics_path`

This appears in UI, coach payload, and pipeline output wiring.

**Recommendation:** keep one canonical key (`analysis_json`) and maintain a translation shim only at external boundaries.

---

## 2) Explainability improvements for thesis report

### 2.1 Add explicit “score decomposition” section (quantitative)
The thesis should include the quality score decomposition already implemented in `repright/summary_v1.py`:
- confidence penalties
- fault severity penalties
- consistency penalties (ROM/tempo variance)

**Recommendation:** document exact penalty table and threshold values, then include one worked example set showing how score reaches final band.

### 2.2 Clarify deterministic vs probabilistic components
Current architecture is mostly deterministic until coaching generation:
1. Pose extraction + metric computation (deterministic pipeline)
2. Rule-based summary/aggregation
3. LLM narrative generation from bounded facts

**Recommendation:** include a pipeline diagram in thesis with this separation, emphasizing that the LLM does not alter analysis metrics.

### 2.3 Add artifact lineage table
Use one table in thesis mapping each artifact to producer and consumer:
- `analysis_v1.json`
- overlay video
- coach payload
- structured coach response

This supports reproducibility claims and examiners’ traceability checks.

---

## 3) Final demo UI/UX improvements implemented

### 3.1 Better score readability and context
- Lift quality now uses color emphasis for fast scanning.
- Added compact metrics row (`Reps`, `Avg ROM`, `Low confidence reps`).

### 3.2 “Why this score?” explainability panel
- Added expandable explanation panel showing top recurring faults and max severity.
- Gives immediate rationale without forcing users to inspect raw JSON.

### 3.3 Faster export and chat hygiene
- Added **Download analysis JSON** button (for live demo evidence + thesis appendix collection).
- Added **Clear current chat** sidebar action for cleaner repeated demos without creating a new thread.

---

## 4) Suggested post-lock housekeeping (non-blocking)

1. Add `.gitignore` patterns for temp backups (`*.bak*`, `_tmp_*`, ad-hoc zip dumps) if not already covered.
2. Add one script `scripts/audit_repo_hygiene.py` to fail CI when temp artifacts are reintroduced.
3. Add a one-page `ARCHITECTURE_LOCK.md` documenting canonical interfaces and immutable schema fields.

---

## 5) Risk level assessment

- **Low risk**: UI improvements merged in this update are presentation-only and do not change analysis algorithm outputs.
- **Medium risk if deferred**: retaining duplicate backup/temp files can cause confusion during final handoff and thesis submission package assembly.
- **High confidence**: core deterministic analysis-to-coach payload path is structured and auditable with stable artifacts.
