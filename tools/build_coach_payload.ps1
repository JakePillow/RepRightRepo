param(
  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$Analyzer,

  [Parameter(Mandatory = $true)]
  [Alias("Out")]
  [ValidateNotNullOrEmpty()]
  [string]$OutPath,

  [Parameter(Mandatory = $false)]
  [AllowNull()]
  [string]$Message = "",

  [Parameter(Mandatory = $false)]
  [double]$LoadKg = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Repo root = parent of /tools
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Py       = Join-Path $RepoRoot ".venv\Scripts\python.exe"

# Normalize paths
$AnalyzerJson = Resolve-Path -LiteralPath (Join-Path $RepoRoot $Analyzer) -ErrorAction SilentlyContinue
if (-not $AnalyzerJson) {
  # If already absolute / valid as given
  if (Test-Path -LiteralPath $Analyzer) {
    $AnalyzerJson = (Resolve-Path -LiteralPath $Analyzer).Path
  } else {
    throw "AnalyzerJson not found: $Analyzer"
  }
} else {
  $AnalyzerJson = $AnalyzerJson.Path
}

# Ensure python exists
if (-not (Test-Path -LiteralPath $Py)) { throw "Python not found: $Py" }

# Ensure output directory exists
$OutFull = Join-Path $RepoRoot $OutPath
$OutDir  = Split-Path -Parent $OutFull
if ($OutDir -and -not (Test-Path -LiteralPath $OutDir)) {
  New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

# Always pass a non-null message to argparse
$Msg = [string]$Message

# Build args (order doesn't matter, but keep consistent)
$args = @(
  "-m", "repright.coach_payload",
  "--analyzer-json", $AnalyzerJson,
  "--message", $Msg,
  "--out", $OutFull
)

if ($LoadKg -gt 0) {
  $args += @("--load-kg", [string]$LoadKg)
}

Push-Location -LiteralPath $RepoRoot
try {
  & $Py @args
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
  Pop-Location
}

# sanity
Test-Path -LiteralPath $OutFull | Out-Host
Write-Host "Wrote payload: $OutFull" -ForegroundColor Green