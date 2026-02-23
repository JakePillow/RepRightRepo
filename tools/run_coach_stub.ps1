param(
  [Parameter(Mandatory=$true)][string]$Payload,
  [string]$Out = ".\_out\last_coach_response.json",
  [string]$Py = ".\.venv\Scripts\python.exe"
)

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

if (-not (Test-Path -LiteralPath $Py)) { throw "Python not found: $Py" }
if (-not (Test-Path -LiteralPath $Payload)) { throw "Payload not found: $Payload" }

& $Py -m repright.coach_stub --payload $Payload --out $Out
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# print the response text
$j = Get-Content $Out -Raw | ConvertFrom-Json
$j.text
