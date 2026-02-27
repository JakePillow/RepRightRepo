param(
  [Parameter(Mandatory=$true)][string]$OutDir,
  [string]$Py = "py",
  [int]$MaxVideos = 0
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot

function Resolve-RepoPath([string]$PathValue) {
  if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
  return (Join-Path $RepoRoot $PathValue)
}

function Find-Label([string]$FileName) {
  $hit = Get-ChildItem -Path $RepoRoot -Recurse -File -Filter $FileName -ErrorAction SilentlyContinue |
         Select-Object -First 1
  if (-not $hit) { throw "Labels file not found anywhere under repo: $FileName" }
  return $hit.FullName
}

$OutFull = Resolve-RepoPath $OutDir
if (-not (Test-Path $OutFull)) { New-Item -ItemType Directory -Force -Path $OutFull | Out-Null }

$Bench = Find-Label "bench_labels.csv"
$Curl  = Find-Label "curl_labels.csv"
$Dead  = Find-Label "deadlift_labels.csv"
$Squat = Find-Label "squat_labels.csv"

Write-Host "Using labels:"
Write-Host "  Bench: $Bench"
Write-Host "  Curl : $Curl"
Write-Host "  Dead : $Dead"
Write-Host "  Squat: $Squat"

$Args = @(
  "-m","repright.eval_cli",
  "--outdir",$OutFull,
  "--repo-root",$RepoRoot,
  "--labels",$Bench,
  "--labels",$Curl,
  "--labels",$Dead,
  "--labels",$Squat
)

if ($MaxVideos -gt 0) {
  $Args += @("--max-videos", "$MaxVideos")
}

$env:PYTHONPATH = $RepoRoot

& $Py @Args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[OK] Wrote eval outputs to: $OutFull"
