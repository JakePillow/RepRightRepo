param(
    [string]$Python = "..\.venv\Scripts\python.exe",
    [string]$GroundTruth = "data\eval\ground_truth.csv",
    [string]$ResultsCsv = "data\eval\results_final.csv",
    [string]$SummaryJson = "data\eval\eval_summary.json",
    [string]$Tag = "final_locked_run",
    [string]$FiguresDir = "data\eval\figures_final",
    [string]$RunsRoot = "runs",
    [switch]$SkipVerify
)

$ErrorActionPreference = "Stop"

function Assert-Path([string]$PathValue, [string]$Label) {
    if (!(Test-Path $PathValue)) {
        throw "$Label not found: $PathValue"
    }
}

Write-Host "[1/5] Preconditions"
Assert-Path $Python "Python interpreter"
Assert-Path $GroundTruth "Ground-truth CSV"
Assert-Path "scripts\evaluate_dataset.py" "evaluate_dataset.py"
Assert-Path "scripts\summarize_eval.py" "summarize_eval.py"
Assert-Path "scripts\generate_ch4_figures.py" "generate_ch4_figures.py"

if (!(Test-Path (Split-Path $ResultsCsv -Parent))) {
    New-Item -ItemType Directory -Force -Path (Split-Path $ResultsCsv -Parent) | Out-Null
}
if (!(Test-Path $FiguresDir)) {
    New-Item -ItemType Directory -Force -Path $FiguresDir | Out-Null
}

if (-not $SkipVerify) {
    Write-Host "[2/5] Verifying deadlift lockout orientation"
    if (Test-Path "scripts\verify_deadlift_lockout.py") {
        & $Python scripts\verify_deadlift_lockout.py --ground $GroundTruth --runs-root $RunsRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Deadlift verification failed. Lockout/top detection was not confirmed."
        }
    } else {
        throw "scripts\verify_deadlift_lockout.py not found."
    }
} else {
    Write-Host "[2/5] Skipped deadlift verification by request"
}

Write-Host "[3/5] Removing prior final results"
Remove-Item $ResultsCsv -ErrorAction SilentlyContinue
Remove-Item $SummaryJson -ErrorAction SilentlyContinue

Write-Host "[4/5] Running final locked evaluation"
& $Python scripts\evaluate_dataset.py --ground $GroundTruth --out $ResultsCsv --tag $Tag
if ($LASTEXITCODE -ne 0) { throw "evaluate_dataset.py failed." }

& $Python scripts\summarize_eval.py --in $ResultsCsv --tag $Tag
if ($LASTEXITCODE -ne 0) { throw "summarize_eval.py failed." }

Write-Host "[5/5] Generating Chapter 4 figures"
& $Python scripts\generate_ch4_figures.py --results $ResultsCsv --summary $SummaryJson --runs-root $RunsRoot --outdir $FiguresDir
if ($LASTEXITCODE -ne 0) { throw "generate_ch4_figures.py failed." }

Write-Host "Done. Outputs:"
Write-Host "  Results CSV : $ResultsCsv"
Write-Host "  Summary JSON: $SummaryJson"
Write-Host "  Figures dir : $FiguresDir"
