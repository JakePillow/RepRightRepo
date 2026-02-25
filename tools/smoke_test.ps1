param(
  [string]$VideoPath = "",
  [string]$Py = "python"
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Canonical = 'C:\Users\jakep\OneDrive\Desktop\Dissertation- RepRight\Dissertation-Rep-Right\RepRightRepo\data\raw\deadlift\deadlift_27.mp4'
$RepoRelative = Join-Path $RepoRoot 'data\raw\deadlift\deadlift_27.mp4'

if (-not $VideoPath) {
  if (Test-Path $RepoRelative) { $VideoPath = $RepoRelative }
  elseif (Test-Path $Canonical) { $VideoPath = $Canonical }
  else {
    Write-Error "Deadlift smoke test video not found. Checked: $RepoRelative and $Canonical"
    exit 1
  }
}

$AnalyzerOut = '.\_out\last_analyzer.json'
$PayloadOut = '.\_out\last_coach_payload.json'
$CoachOut = '.\_out\last_coach_response.json'

& (Join-Path $PSScriptRoot 'run_analyzer.ps1') -VideoPath $VideoPath -Exercise deadlift -OutPath $AnalyzerOut -Py $Py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot 'build_coach_payload.ps1') -AnalyzerPath $AnalyzerOut -OutPath $PayloadOut -Message 'Strength focus.' -Py $Py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $PSScriptRoot 'run_coach.ps1') -PayloadPath $PayloadOut -OutPath $CoachOut -Py $Py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$AnalyzerFull = Join-Path $RepoRoot $AnalyzerOut
$PayloadFull = Join-Path $RepoRoot $PayloadOut
$CoachFull = Join-Path $RepoRoot $CoachOut

$AnalyzerObj = Get-Content $AnalyzerFull -Raw | ConvertFrom-Json
$PayloadObj = Get-Content $PayloadFull -Raw | ConvertFrom-Json
$CoachObj = Get-Content $CoachFull -Raw | ConvertFrom-Json

if (-not $AnalyzerObj.reps -or -not $AnalyzerObj.set_summary_v1) { Write-Error 'Analyzer schema check failed'; exit 1 }
if (-not $PayloadObj.rep_table -or -not ($PayloadObj.PSObject.Properties.Name -contains 'analysis_v1')) { Write-Error 'Payload schema check failed'; exit 1 }
if (-not $CoachObj.response_text -or $CoachObj.schema_version -ne 'coach_response_v1') { Write-Error 'Coach schema check failed'; exit 1 }

Write-Host "Produced analyzer json path: $AnalyzerFull"
Write-Host "Produced coach payload path: $PayloadFull"
Write-Host "Produced coach response path: $CoachFull"
Write-Host 'Response preview:'
($CoachObj.response_text -split "`n") | Select-Object -First 15 | ForEach-Object { Write-Host $_ }
