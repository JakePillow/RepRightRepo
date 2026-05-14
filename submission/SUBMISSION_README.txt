RepRight - Pose Analysis and Exercise Coaching Pipeline
Faculty of ICT, University of Malta - Thesis Submission
Submitted: May 14, 2026

================================================================================
ARTIFACT CONTENTS
================================================================================

./repright/          - Core analysis and coaching modules
                      - analyser.py: video->pose extraction pipeline
                      - coach_payload.py: structured coach input generation
                      - llm_wrapper.py: LLM coach response generation (CLI: --payload flag)
                      
./scripts/           - Data processing and pipeline orchestration
                      - pipeline.py: main analysis orchestration
                      - extract_all.py: batch video processing
                      
./ui/                - Streamlit interactive coaching interface
                      - streamlit_app.py: browser-based UI
                      
./tools/             - Utility scripts and smoke tests
                      - smoke_test.ps1: end-to-end verification (see VERIFY below)
                      - run_coach.ps1: coach wrapper launcher
                      - build_coach_payload.ps1: payload generator
                      
./data/              - Evaluation ground truth and assessments
  - eval/ground_truth.csv: repo-relative paths to video samples
  - raw-Jakes_PC/    : Sample exercise videos (bench, curl, deadlift, squat)
  
./requirements.txt   - Python dependencies (pinned versions)
./README.md          - Full setup and usage instructions
./LICENSE            - MIT License (for thesis submission)

================================================================================
SETUP (5 minutes)
================================================================================

1. Extract this archive
2. Open PowerShell in the extracted directory
3. Create a virtual environment:
   python -m venv .venv
   
4. Activate the environment:
   .\.venv\Scripts\Activate.ps1
   
5. Install dependencies:
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt

================================================================================
VERIFY FUNCTIONALITY
================================================================================

The smoke test validates the end-to-end pipeline:
  .	ools\smoke_test.ps1

Expected output:
  - Analyzer produces JSON with rep metrics
  - Coach payload generated from analysis
  - Coach response (via OpenAI or stub) produces coaching text
  - All schemas pass validation

Dependencies: Requires sample video at data/raw-Jakes_PC/deadlift/deadlift_27.mp4

================================================================================
RUN THE UI
================================================================================

Start the Streamlit interface:
  .un_ui.cmd

This launches the interactive coaching UI at http://localhost:8502
- Upload or select exercise videos
- View pose analysis overlays
- Get personalized coach feedback

================================================================================
CLI USAGE
================================================================================

Coach wrapper:
  python -m repright.llm_wrapper --payload C:\path	o\payload.json --out response.json

Analyzer:
  python -m repright.analyser --video C:\path	oideo.mp4 --exercise deadlift

(See README.md for full CLI documentation)

================================================================================
REPRODUCIBILITY NOTES
================================================================================

- All package versions are pinned in requirements.txt
- Paths are repo-relative (no machine-specific absolute paths)
- Sample data included in data/raw-Jakes_PC/ directory
- Ground truth evaluation CSV uses repo-relative paths
- Evaluation can be run via scripts/pipeline.py on your own videos

================================================================================
KNOWN LIMITATIONS
================================================================================

- Raw training videos (2000+ hours) are not included; evaluation paths reference
  the data/raw-Jakes_PC/ subset included for reproducibility testing
  
- Coach response requires valid OPENAI_API_KEY environment variable.
  If not set, the pipeline falls back to a safe stub response.
  
- Streamlit requires a clean Python environment; do not mix system/conda Python.

================================================================================
SUPPORT FILES
================================================================================

README.md            - Full documentation and examples
requirements.txt     - Python dependencies (pinned)
.gitignore           - Filters for .venv, build artifacts, etc.
LICENSE              - MIT License

For questions or issues, see README.md for architecture overview and
design decisions.

================================================================================
END OF SUBMISSION_README.txt
================================================================================
