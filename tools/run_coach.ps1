param(
  [Parameter(Mandatory=$true)][string]$Payload,
  [ValidateSet("stub","gpt")][string]$Mode = "stub",
  [string]$Out = ".\_out\last_coach_response.json",
  [string]$Py = ".\.venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

if (-not (Test-Path -LiteralPath $Py))      { throw "Python not found: $Py" }
if (-not (Test-Path -LiteralPath $Payload)) { throw "Payload not found: $Payload" }

$outDir = Split-Path -Parent $Out
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
  New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

& $Py -m repright.llm_wrapper --payload $Payload --out $Out --mode $Mode
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$j = Get-Content $Out -Raw | ConvertFrom-Json
Write-Output $Out
Write-Output $j.response_text
