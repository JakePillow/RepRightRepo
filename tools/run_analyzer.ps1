param(
  [Parameter(Mandatory=$true)][string]$Video,
  [Parameter(Mandatory=$true)][string]$Exercise,

  # Always prefer venv python by default
  [string]$Py = ".\.venv\Scripts\python.exe",

  [string]$ProcessedRoot = "data/processed",
  [string]$UploadsRoot   = "data/uploads",

  # Optional: write full analyzer JSON here
  [string]$Out = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure we're running from repo root (directory that contains repright/)
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

# Resolve paths early (handles relative paths)
$VideoPath = (Resolve-Path -LiteralPath $Video).Path

if (-not (Test-Path -LiteralPath $Py)) {
  throw "Python not found: $Py (run from repo root, or pass -Py explicitly)"
}
if (-not (Test-Path -LiteralPath $VideoPath)) {
  throw "Video not found: $VideoPath"
}

# Run analyzer module (repright/analyzer.py main())
$argv = @(
  "-m","repright.analyzer",
  "--video",$VideoPath,
  "--exercise",$Exercise,
  "--processed-root",$ProcessedRoot,
  "--uploads-root",$UploadsRoot
)

if ($Out -and $Out.Trim() -ne "") {
  $argv += @("--out",$Out)
}

& $Py @argv
exit $LASTEXITCODE