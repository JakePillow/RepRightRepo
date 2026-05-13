# RepRight

RepRight is a pose-analysis and coaching pipeline for exercise video evaluation. It provides deterministic exercise analysis, coach payload generation, and a Streamlit UI for review.

## Supported setup

- Python 3.10 or 3.11
- `requirements.txt` pins compatible runtime dependencies
- Use a local virtual environment and install dependencies before running

## Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the UI

```powershell
.
un_ui.cmd
```

This uses `.venv\Scripts\python.exe` and starts the Streamlit app at `ui\streamlit_app.py`.

## Coach CLI path

The coach wrapper now supports the documented command line entrypoint:

```powershell
python -m repright.llm_wrapper --payload tmp\analysis.json --out _out\llm_wrapper_cli_probe.json
```

If `OPENAI_API_KEY` is not set, the CLI falls back to a safe stub response.

## Smoke test

A repository-local smoke test is available in `tools\smoke_test.ps1`.

```powershell
.	ools\smoke_test.ps1 -VideoPath data\raw\deadlift\deadlift_27.mp4
```

If the sample video is not present, pass `-VideoPath` explicitly.

## Notes for packaging

- `.venv/` is intentionally ignored and should not be included in the submission archive.
- `tmp/`, scratch files, and local-only artifacts are ignored by `.gitignore`.
- The `RepRightRepo/` nested directory is ignored if present and is not part of the canonical repository.

## Known limitations

- Raw evaluation videos are not included in this repository.
- The Streamlit UI depends on the pinned `requirements.txt` and a working Python virtual environment.
