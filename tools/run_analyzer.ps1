param(
  [Parameter(Mandatory=$true)][string]$VideoPath,
  [Parameter(Mandatory=$true)][ValidateSet('bench','curl','deadlift','squat')][string]$Exercise,
  [Parameter(Mandatory=$true)][string]$OutPath,
  [string]$Py = "python"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
function Resolve-RepoPath([string]$PathValue) {
  if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return (Join-Path $RepoRoot $PathValue)
}

$VideoFull = Resolve-RepoPath $VideoPath
$OutFull = Resolve-RepoPath $OutPath
$OutDir = Split-Path -Parent $OutFull
if ($OutDir -and -not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

& $Py -m repright.analyzer_cli --video-path $VideoFull --exercise $Exercise --out $OutFull
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Analyzer JSON: $OutFull"
