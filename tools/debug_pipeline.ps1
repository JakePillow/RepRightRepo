param(
  [ValidateSet("bench","squat","curl","deadlift","all")]
  [string]$Exercise = "all",

  [string]$RawRoot = "data/raw",
  [string]$ProcessedRoot = "data/processed",

  [int]$MaxVideos = 0,
  [int]$TopN = 20,
  [int]$SmokeN = 3,

  [switch]$ForceExtract
)

$ErrorActionPreference = "Stop"

function Say($msg)  { Write-Host $msg -ForegroundColor Cyan }
function Ok($msg)   { Write-Host $msg -ForegroundColor Green }
function Warn($msg) { Write-Host $msg -ForegroundColor Yellow }
function Fail($msg) { Write-Host $msg -ForegroundColor Red }

# ---- resolve paths (works in scripts; doesn't rely on $PSScriptRoot in console) ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$PyExe     = Join-Path $RepoRoot ".venv\Scripts\python.exe"

function RunPy([string[]]$PyArgs) {
  & $PyExe @PyArgs
  if ($LASTEXITCODE -ne 0) {
    Fail "Python failed (exit=$LASTEXITCODE): $PyExe $($PyArgs -join ' ')"
    exit $LASTEXITCODE
  }
}

Set-Location $RepoRoot

Say "== ENV CHECK =="
Ok  "Repo root: $RepoRoot"
Ok  "Venv python: $PyExe"

if (-not (Test-Path ".git")) { Fail "Not in repo root (no .git found)."; exit 1 }
if (-not (Test-Path $PyExe)) {
  Fail "Venv python not found: $PyExe"
  Fail "Create it: py -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt"
  exit 1
}

$env:PYTHONPATH = (Resolve-Path ".\scripts").Path + ";" + (Resolve-Path ".").Path
Ok "PYTHONPATH set: $env:PYTHONPATH"

Say "python executable (from sys.executable):"
RunPy @("-c","import sys; print(sys.executable)")

Say "python version:"
RunPy @("-c","import sys; print(sys.version)")

Say "deps check:"
RunPy @("-c","import numpy as np; print('numpy', np.__version__)")
RunPy @("-c","import cv2; print('cv2', cv2.__version__)")
RunPy @("-c","import mediapipe as mp; print('mediapipe', mp.__version__)")

Say "`n== SCRIPT CHECK =="
$must = @(
  "scripts/extract_poses.py",
  "scripts/compute_rep_metrics.py",
  "scripts/evaluate.py",
  "scripts/run_cli.py",
  "scripts/engine.py"
)
foreach ($p in $must) { if (-not (Test-Path $p)) { Fail "Missing: $p"; exit 1 } }
Ok "Scripts present."

function EnsurePoseForExercise([string]$ex) {
  $poseDir = Join-Path $ProcessedRoot ("pose/" + $ex)
  if (-not (Test-Path $poseDir)) { New-Item -ItemType Directory -Force $poseDir | Out-Null }

  $npzCount = @(Get-ChildItem $poseDir -Filter "*.npz" -File -ErrorAction SilentlyContinue).Count
  if (($npzCount -gt 0) -and (-not $ForceExtract)) {
    Ok "Pose NPZ exists for $ex ($npzCount files). Skipping extract_poses."
    return
  }

  Warn "Running extract_poses for $ex (ForceExtract=$ForceExtract)..."
  $py = @("scripts/extract_poses.py","--exercise",$ex,"--raw-root",$RawRoot,"--processed-root",$ProcessedRoot)
  if ($MaxVideos -gt 0) { $py += @("--max-videos",$MaxVideos) }
  RunPy $py
  Ok "extract_poses done for $ex"
}

function ComputeMetrics([string]$ex) {
  Say "`n== METRICS ($ex) =="
  $py = @("scripts/compute_rep_metrics.py","--exercise",$ex,"--processed-root",$ProcessedRoot)
  if ($MaxVideos -gt 0) { $py += @("--max-videos",$MaxVideos) }
  RunPy $py
  Ok "compute_rep_metrics done for $ex"
}

function EvaluateAndReport() {
  Say "`n== EVALUATE =="
  RunPy @("scripts/evaluate.py")
  Ok "Wrote data/reports/eval_summary.csv"

  $csvPath = "data/reports/eval_summary.csv"
  if (-not (Test-Path $csvPath)) { Fail "Missing report: $csvPath"; exit 1 }

  $csv = Import-Csv $csvPath

  Say "`n== STATUS COUNTS =="
  $csv | Group-Object status | Sort-Object Count -Descending | Format-Table Count, Name -Auto

  Say "`n== WORST MISMATCHES (Top $TopN) =="
  $csv |
    Where-Object { $_.status -eq "ok" } |
    Select-Object exercise, expected_reps, pred_reps, camera_angle, video_rel |
    Sort-Object @{Expression={ [math]::Abs([int]$_.expected_reps - [int]$_.pred_reps) }; Descending=$true } |
    Select-Object -First $TopN |
    Format-Table -Auto

  return $csv
}

function SmokeWorstClips([object[]]$csv, [string]$ex, [int]$n=3) {
  Say "`n== SMOKE TEST WORST $n CLIPS ($ex) =="

  $worst = $csv |
    Where-Object { $_.status -eq "ok" -and $_.exercise -eq $ex } |
    Sort-Object @{Expression={ [math]::Abs([int]$_.expected_reps - [int]$_.pred_reps) }; Descending=$true } |
    Select-Object -First $n

  foreach ($r in $worst) {
    $vid = $r.video_rel
    Say "`n--- CLI: $($r.exercise) exp=$($r.expected_reps) pred=$($r.pred_reps) angle=$($r.camera_angle) ---"
    RunPy @("scripts/run_cli.py", $vid, "--exercise", $ex)
  }
}

$exList = if ($Exercise -eq "all") { @("bench","squat","curl","deadlift") } else { @($Exercise) }

foreach ($ex in $exList) {
  EnsurePoseForExercise $ex
  ComputeMetrics $ex
}

$csv = EvaluateAndReport

foreach ($ex in $exList) {
  SmokeWorstClips $csv $ex $SmokeN
}

Ok "`nDONE."
