  [Parameter(Mandatory=$true)]
  [string]$Analyzer,

  [Parameter(Mandatory=$true)]
  [string]$Out,

  [Parameter(Mandatory=$false)]
  [string]$Message = ""
)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
$Py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$AnalyzerJson = $Analyzer
$LoadKg = 0  # Default value, override if needed
Set-Location $RepoRoot

if (-not (Test-Path -LiteralPath $Py)) { throw "Python not found: $Py" }
if (-not (Test-Path -LiteralPath $AnalyzerJson)) { throw "AnalyzerJson not found: $AnalyzerJson" }

$args = @(
  "-m","repright.coach_payload",
  "--analyzer-json",$AnalyzerJson,
  "--message",$Message,
  "--out",$Out
)

if ($LoadKg -gt 0) {
  $args += @("--load-kg",$LoadKg)
}

& $Py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# sanity
Test-Path $Out | Out-Host
