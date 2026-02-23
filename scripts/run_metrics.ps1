param(
  [Parameter(Mandatory=$true)][string]$npz,
  [Parameter(Mandatory=$true)][string]$exercise,
  [string]$meta = "",
  [double]$fps = 0,
  [string]$out = ""
)

$ErrorActionPreference = "Stop"
$Py = ".\.venv\Scripts\python.exe"

$cmd = @("-m","scripts.compute_rep_metrics_cli","--npz",$npz,"--exercise",$exercise)
if ($meta) { $cmd += @("--meta",$meta) }
if ($fps -gt 0) { $cmd += @("--fps",$fps) }
if ($out) { $cmd += @("--out",$out) }

& $Py @cmd
