# RepRight Sunday Lock Gap Report (A–G)

## A) Analyzer output contract: `analysis_v1`
- **Status before patch:** Partial/non-compliant.
- **Acceptance requirement:** Analyzer JSON MUST include `schema_version: "analysis_v1"`.
- **Gaps found:** Fault objects were underspecified (`faults_v1` only code/evidence dict), schema marker was inconsistent, and required rep fields needed hard lock behavior.
- **Fixes:** `scripts/compute_rep_metrics.py` now emits locked keys for every rep (`confidence_v1` always present, `faults_v1` always list with `code,severity,value,threshold,evidence`) and `set_summary_v1` at top level, with explicit `schema_version: "analysis_v1"`.

## B) Coach payload contract: `coach_payload_v1`
- **Status before patch:** Partial/non-compliant.
- **Acceptance requirement:** Payload JSON MUST include `schema_version: "coach_payload_v1"`.
- **Gaps found:** `rep_table[*].faults` only carried fault codes; required compact fields and highlight keys were missing.
- **Fixes:** `repright/coach_payload.py` now outputs required structure with full fault objects, required rep_table fields, `schema_version: "coach_payload_v1"`, and `highlights` keys (`fast_eccentric_reps`, `asym_rom_elbow_reps`, tempo min/max, overlay/metrics paths).

## C) Coach response contract: `coach_response_v1`
- **Status before patch:** Mostly compliant but CLI overexposed flags.
- **Acceptance requirement:** Coach output JSON MUST include `schema_version: "coach_response_v1"`.
- **Gaps found:** Wrapper/CLI mismatch risk due to optional `--mode` plumbing.
- **Fixes:** `repright/llm_wrapper.py` CLI locked to `--payload` + `--out`; output includes explicit `schema_version: "coach_response_v1"` and `mode: stub`.

## D) Single orchestrator class
- **Status before patch:** Present but signature drift and path contract needed tightening.
- **Fixes:** `repright/analyser.py::RepRightAnalyzer.run(video_path, exercise_label, out_path, options)` now serves CLI/UI/programmatic calls and writes deterministic artifact metadata. `repright/core.py` + `repright/analyser_cli.py` route through this class.

## E) Deterministic PowerShell wrappers
- **Status before patch:** Partial.
- **Gaps found:** `run_coach.ps1` passed unsupported `--mode`; rooted path handling could be fragile.
- **Fixes:** All wrappers now use required param names, create output dirs, call operator `&`, exit propagation, and robust rooted/relative path resolution.

## F) Exercise-aware driver selection
- **Status before patch:** Partial.
- **Gaps found:** Deadlift fallback risk via filename inference.
- **Fixes:** `scripts/pipeline.py` passes explicit exercise override into `scripts/extract_all.py`, preventing elbow-only leakage on deadlift/squat routing.

## G) UI shell (minimal chat)
- **Status before patch:** Compliant baseline.
- **Acceptance points:**
  - Keeps chat history in Streamlit session state.
  - Rerun uses last analyzer/payload unless user uploads a new video.
- **Fixes:** Thin chat shell in `ui/streamlit_app.py` uses orchestrator + payload builder + coach runner with follow-up context persistence and rerun-from-last-analysis behavior.

## Patched files
- `scripts/compute_rep_metrics.py`
- `repright/analyser.py`
- `repright/analyser_cli.py`
- `repright/core.py`
- `repright/coach_payload.py`
- `repright/llm_wrapper.py`
- `tools/run_analyser.ps1`
- `tools/build_coach_payload.ps1`
- `tools/run_coach.ps1`
- `tools/smoke_test.ps1`
- `GAP_REPORT.md`
