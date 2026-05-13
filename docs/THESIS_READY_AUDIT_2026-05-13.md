# RepRight Thesis-Ready Repository Audit

Date: 2026-05-13
Scope: `C:\Projects\RepRightRepo\RepRightRepo` plus the untracked nested copy at `RepRightRepo\`

## Executive verdict

The core Python source compiles, and the main analysis architecture is understandable: video upload/staging, MediaPipe pose extraction, deterministic metric computation, overlay generation, coach payload construction, and Streamlit UI. However, the repository is not yet thesis-submission clean. The largest risks are reproducibility, repository packaging, and a broken documented coach CLI path.

Thesis readiness rating: **Amber / not clean enough to submit unchanged**.

Recommended target before submission: fix the critical items below, then submit a trimmed source package plus a separate evidence/data package.

## Critical fixes before submission

### 1. The main repo contains an untracked nested full repository

Evidence:
- `git status --short --branch` from the main root reports `?? RepRightRepo/`.
- The nested directory is about 856 MB and contains its own `.git`, `.venv`, source, generated data, uploads, and processed runs.
- The nested `.venv` alone is about 600 MB.
- The nested `data` directory is about 237 MB.

Risk:
- If the folder is zipped manually, the submission can include a whole duplicate repo, virtual environment, raw uploads, generated runs, and a second git history.
- Markers may review the wrong copy. The active IDE path points at `RepRightRepo/RepRightRepo/scripts/extract_all.py`, which is inside the nested copy, while the main git repo sees that whole copy as untracked.

Action:
- Decide which tree is canonical.
- If `C:\Projects\RepRightRepo\RepRightRepo` is canonical, move or delete the nested `RepRightRepo/` before packaging.
- If the nested copy is canonical, promote it intentionally and avoid submitting the parent wrapper.

### 2. The documented coach CLI path is broken

Evidence:
- `tools/run_coach.ps1:18` calls `python -m repright.llm_wrapper --payload ... --out ...`.
- `repright/llm_wrapper.py` has no CLI `main()` or `if __name__ == "__main__"` block.
- Verification command:
  - `python -m repright.llm_wrapper --payload tmp\analysis.json --out _out\llm_wrapper_cli_probe.json`
  - Result: `exit=0 exists=False`.
- `python -m repright.llm_wrapper --help` also exits with no help text.

Risk:
- `tools/smoke_test.ps1` can silently fail to produce the expected coach response file.
- This undermines the claimed end-to-end reproducibility path.

Action:
- Add a CLI entrypoint to `repright/llm_wrapper.py`, or change `tools/run_coach.ps1` to call `repright.coach_stub` / another real CLI.
- Re-run `tools/smoke_test.ps1` with a known local video after the fix.

### 3. `run_ui.cmd` uses a broken main virtualenv

Evidence:
- `run_ui.cmd:5` uses `%REPO_ROOT%.venv\Scripts\python.exe`.
- The main `.venv` exists but lacks runtime packages:
  - `.venv\Scripts\python.exe -m streamlit --version` fails with `No module named streamlit`.
  - `.venv\Scripts\python.exe -c "import mediapipe"` fails with `No module named 'mediapipe'`.
- The nested `.venv` has dependencies and Python 3.10.11, but it is inside the untracked nested repo.

Risk:
- A marker running `run_ui.cmd` from the main submitted repo gets an immediate failure.

Action:
- Rebuild the canonical virtualenv from `requirements.txt`, or do not submit `.venv` and document setup clearly in a README.
- Prefer `python -m venv .venv`, `pip install -r requirements.txt`, then `run_ui.cmd`.

### 4. Requirements and actual working environment disagree

Evidence:
- `requirements.txt` pins `mediapipe==0.10.21` and `protobuf==4.25.8`.
- The nested working `.venv` has `mediapipe==0.10.5` and `protobuf==3.20.3`.
- The main and nested repo Python versions also differ:
  - main `.venv`: Python 3.13.1
  - nested `.venv`: Python 3.10.11
  - devcontainer: Python 3.11 image

Risk:
- Results may not be reproducible across machines.
- MediaPipe compatibility is sensitive to Python and protobuf versions.

Action:
- Pick one supported runtime, ideally Python 3.10 or 3.11.
- Regenerate/validate `requirements.txt` from that runtime.
- Add a short setup verification command to README.

### 5. Contract docs and code disagree on coach payload schema

Evidence:
- `GAP_REPORT.md` states the required payload schema is `coach_payload_v1`.
- `repright/coach_payload.py:282` emits `schema_version: "coach_payload_v2"`.
- `repright/coach_stub.py:77` still describes the payload as `coach_payload_v1`.

Risk:
- The thesis may claim a locked artifact contract that the code no longer follows.

Action:
- Either revert the emitted payload marker to `coach_payload_v1`, or update all docs, smoke checks, and thesis text to say `coach_payload_v2`.
- Add one schema assertion test for payload generation.

## High-priority cleanup

### 6. Submission package contains tracked scratch/build artifacts

Tracked artifacts include:
- `_gpt_inspect (2).zip`
- `_gpt_inspect.zip`
- `_gpt_inspect_20260302_135308.zip`
- `gpt_inspect.zip`
- `_tmp_*.py`
- `_tmp_*.ps1`
- `repright/llm_wrapper.py.bak_20260223_150746`
- `scripts/evaluate.py.bak`
- `scripts/run_cli.py.bak`
- `scripts/make_overlay_from_npz.py.bak_*`
- `tools/build_coach_payload.ps1.bak_20260223_193500`
- `scripts/__pycache__/*.pyc`
- `tmp/analysis.json`

Risk:
- Looks unfinished.
- Makes the repo harder to assess.
- Backup files can contradict active files.

Action:
- Remove from git or move into an external archive not included in source submission.
- Update `.gitignore` with `*.bak*`, `_tmp_*`, `*.zip`, `tmp/`, and `__pycache__/`.

### 7. No README or LICENSE was found at the main root

Evidence:
- No `README*` file found.
- No `LICENSE*` file found.
- `.devcontainer/devcontainer.json` tries to open `README.md`, which does not exist.

Risk:
- A thesis examiner cannot quickly tell how to install, run, evaluate, and reproduce the artifact.

Action:
- Add `README.md` with:
  - project purpose
  - supported Python version
  - setup commands
  - UI command
  - CLI smoke command
  - data/evaluation notes
  - known limitations
- Add a license or explicitly state repository use restrictions for thesis submission.

### 8. Evaluation data points to machine-specific paths

Evidence:
- `data/eval/ground_truth.csv` contains paths like:
  - `C:\dev\RepRightRepo_PUSHFIX\data\raw-Jakes_PC\bench\bench press_1.mp4`

Risk:
- Batch evaluation cannot run on another machine without path rewriting.
- Reproducibility claims are weakened.

Action:
- Make paths repo-relative where possible.
- Document where raw videos are stored if they cannot be submitted.
- Add a script flag such as `--raw-root` to resolve ground-truth paths portably.

### 9. Smoke test contains a personal absolute path

Evidence:
- `tools/smoke_test.ps1:7` uses:
  - `C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\...`

Risk:
- Fails for markers and on clean machines.

Action:
- Replace with repo-relative demo asset, or require `-VideoPath` with a clear error message.

### 10. Docs contain mojibake / encoding corruption

Evidence:
- `FINAL_AUDIT_REPORT.md` and `GAP_REPORT.md` render characters such as `â€“`, `â€œ`, and `âœ...`.
- `.devcontainer/devcontainer.json` prints `âœ...` in `updateContentCommand`.

Risk:
- Looks unpolished in a final thesis appendix.

Action:
- Normalize docs to UTF-8 and replace corrupted punctuation.

## Code quality and architecture notes

### Strengths

- `scripts/pipeline.py` has a clear single orchestration path and writes `analysis_v1.json`.
- `repright/analyser.py` provides a compact programmatic wrapper and stages uploaded files with exercise-tagged names.
- `repright/schema/validate_analysis.py` provides at least a minimal top-level schema guard.
- `repright/summary_v1.py` makes quality scoring explainable and deterministic.
- `repright/llm_wrapper.py` grounds coaching responses in a bounded facts object and sanitizes generated output.
- Streamlit UI code is split across services, view models, components, state, config, and theme files.

### Risks

- `repright/analyser.py:41-68` still has multiple `TypeError` compatibility fallbacks around `run_full_pipeline`, despite `scripts/pipeline.py:89-94` now having a stable signature.
- `repright/schema/validate_analysis.py` checks only a minimal subset of the `analysis_v1` structure and does not assert schema version equality.
- `repright/coach_stub.py:12-20` reads `faults`, but the current payload uses `faults_v1`; the stub can miss faults.
- `build_final_results.py` assumes `data\eval\ground_truth_custom.csv` and `data\eval_custom`, but those are not present in the main repo.
- `run_custom_eval.py` has the same missing custom-data assumption.
- `tools/run_eval.ps1` searches recursively for label files that are not present in the main repo.

## Verification performed

Commands/checks run:
- `git status --short --branch` in main and nested repos.
- `rg --files` and tracked-file inventory with `git ls-files`.
- `python -m compileall -q repright scripts ui` in main repo: passed.
- Nested `.venv` compile check: passed.
- `python -m pytest -q` in main and nested envs: not runnable, `pytest` is not installed.
- Main `.venv` dependency import check: failed, missing `mediapipe` and `streamlit`.
- Nested `.venv` dependency import check: passed for `mediapipe`, `cv2`, `streamlit`, `numpy`, and `pandas`.
- `python -m repright.llm_wrapper --payload ... --out ...`: exits 0 but creates no output file.
- `run_ui.cmd --server.headless true`: fails because main `.venv` lacks Streamlit.

## Two-day triage plan

Day 1, first pass:
1. Fix `repright.llm_wrapper` CLI or update `tools/run_coach.ps1`.
2. Decide and clean the canonical repo tree. Remove the nested duplicate from the submission root.
3. Rebuild a clean `.venv` from the selected Python version and `requirements.txt`.
4. Add `README.md` with exact commands.

Day 1, second pass:
1. Remove tracked scratch, zip, `.bak`, `.pyc`, and `tmp` artifacts.
2. Align `coach_payload_v1` vs `coach_payload_v2` across code, docs, and thesis.
3. Replace absolute local paths in smoke/evaluation workflows.

Day 2:
1. Run one known-good video through analyzer, payload builder, coach response, and UI.
2. Export the final `analysis_v1.json`, overlay, payload, and response as evidence artifacts.
3. Run batch evaluation if raw data is available; otherwise document why data is external and how to reproduce it.
4. Re-open the final repo from a clean terminal and follow only the README.

## Submission recommendation

Do not submit the folder exactly as it is today. Submit a cleaned canonical source tree, and keep raw/generated videos and large local environment files in a separate evidence bundle or external storage reference. The thesis can honestly present the system as a deterministic pose-analysis pipeline with optional LLM coaching, but the repository must demonstrate that with one reliable, documented end-to-end command path.
