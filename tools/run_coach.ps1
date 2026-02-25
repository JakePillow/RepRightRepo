param(
  [Parameter(Mandatory=$true)][string]$PayloadPath,
  [Parameter(Mandatory=$true)][string]$OutPath,
  [string]$Py = "python"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
function Resolve-RepoPath([string]$PathValue) {
  if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return (Join-Path $RepoRoot $PathValue)
}

$PayloadFull = Resolve-RepoPath $PayloadPath
$OutFull = Resolve-RepoPath $OutPath
$OutDir = Split-Path -Parent $OutFull
if ($OutDir -and -not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

& $Py -m repright.llm_wrapper --payload $PayloadFull --out $OutFull
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Coach response JSON: $OutFull"
