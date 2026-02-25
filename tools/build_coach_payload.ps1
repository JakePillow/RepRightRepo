param(
  [Parameter(Mandatory=$true)][string]$AnalyzerPath,
  [Parameter(Mandatory=$true)][string]$OutPath,
  [string]$Message = "",
  [Nullable[Double]]$LoadKg = $null,
  [string]$Py = "python"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
function Resolve-RepoPath([string]$PathValue) {
  if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return (Join-Path $RepoRoot $PathValue)
}

$AnalyzerFull = Resolve-RepoPath $AnalyzerPath
$OutFull = Resolve-RepoPath $OutPath
$OutDir = Split-Path -Parent $OutFull
if ($OutDir -and -not (Test-Path $OutDir)) { New-Item -ItemType Directory -Force -Path $OutDir | Out-Null }

$Args = @('-m','repright.coach_payload','--analyzer-json',$AnalyzerFull,'--out',$OutFull,'--message',$Message)
if ($null -ne $LoadKg) { $Args += @('--load-kg', [string]$LoadKg) }
& $Py @Args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Coach payload JSON: $OutFull"
