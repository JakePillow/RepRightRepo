$ErrorActionPreference = "Stop"
$File = Join-Path (Get-Location).Path "scripts\compute_rep_metrics.py"
if (-not (Test-Path -LiteralPath $File)) { throw "Not found: $File" }

$ts  = Get-Date -Format "yyyyMMdd_HHmmss"
$bak = "$File.bak_gate_$ts"
Copy-Item -LiteralPath $File -Destination $bak -Force
Write-Host "Backup: $bak" -ForegroundColor DarkGray

$src = Get-Content -LiteralPath $File -Raw -Encoding UTF8

function Assert-Regex([string]$Text,[string]$Pattern,[string]$Msg) {
  if ($Text -notmatch $Pattern) { throw $Msg }
}

# 0) Ensure ExerciseParams has max_trunk_angle_deg
if ($src -notmatch 'max_trunk_angle_deg') {
  $patternParamsTail = '(?ms)(class\s+ExerciseParams:\s*\r?\n(?:\s+.*\r?\n)+?\s+max_elbow_rom_asym_deg:\s*float\s*=\s*18\.0\s*\r?\n)'
  Assert-Regex $src $patternParamsTail "Could not find ExerciseParams tail to insert max_trunk_angle_deg."
  $src = [regex]::Replace($src, $patternParamsTail, "`$1" + "    max_trunk_angle_deg: float = 65.0  # placeholder; tune later`r`n", 1)
  Write-Host "Added ExerciseParams.max_trunk_angle_deg." -ForegroundColor Green
} else {
  Write-Host "ExerciseParams.max_trunk_angle_deg already present." -ForegroundColor DarkGray
}

# 1) Replace biomechanics/fault block with exercise-gated version
$patternBlock = '(?ms)^\s*# Phase2 biomech_v1: angle ROM per rep.*?^\s*# Tempo faults'
Assert-Regex $src $patternBlock "Could not find biomech/fault block (anchor moved)."

$replacement = @"
        # Phase2 biomech_v1: exercise-aware biomechanics + faults
        biomech_v1: Dict[str, Any] = {"angles": {}}
        faults_v1: List[Dict[str, Any]] = []

        # --- Bench/Curl: elbow ROM + asym (only)
        if ex in ("bench", "curl"):
            if elbow_L is not None and elbow_R is not None:
                aL = elbow_L[start : end + 1]
                aR = elbow_R[start : end + 1]

                minL = float(np.nanmin(aL)) if np.isfinite(aL).any() else float("nan")
                maxL = float(np.nanmax(aL)) if np.isfinite(aL).any() else float("nan")
                romL = float(maxL - minL) if np.isfinite(minL) and np.isfinite(maxL) else float("nan")

                minR = float(np.nanmin(aR)) if np.isfinite(aR).any() else float("nan")
                maxR = float(np.nanmax(aR)) if np.isfinite(aR).any() else float("nan")
                romR = float(maxR - minR) if np.isfinite(minR) and np.isfinite(maxR) else float("nan")

                side = "L" if (np.isfinite(romL) and (not np.isfinite(romR) or romL >= romR)) else "R"
                if side == "L":
                    biomech_v1["angles"]["elbow"] = {"side": "L", "min_deg": minL, "max_deg": maxL, "rom_deg": romL, "valid_frac": 1.0}
                    dom_rom = romL
                else:
                    biomech_v1["angles"]["elbow"] = {"side": "R", "min_deg": minR, "max_deg": maxR, "rom_deg": romR, "valid_frac": 1.0}
                    dom_rom = romR

                if np.isfinite(dom_rom) and dom_rom < params.min_elbow_rom_deg:
                    faults_v1.append(_fault(
                        "PARTIAL_ROM_ELBOW",
                        "warn",
                        dom_rom,
                        params.min_elbow_rom_deg,
                        f"elbow_rom_deg<{params.min_elbow_rom_deg}",
                    ))

                if np.isfinite(romL) and np.isfinite(romR):
                    asym = float(abs(romL - romR))
                    if asym > params.max_elbow_rom_asym_deg:
                        faults_v1.append(_fault(
                            "ASYM_ROM_ELBOW",
                            "info",
                            asym,
                            params.max_elbow_rom_asym_deg,
                            f"|rom_L-rom_R|>{params.max_elbow_rom_asym_deg}",
                        ))

        # --- Deadlift/Squat: trunk angle (proxy) (only)
        if ex in ("deadlift", "squat"):
            if pose is not None and isinstance(pose, np.ndarray) and pose.ndim == 3 and pose.shape[1] >= 25:
                trunk = _trunk_angle_deg_series(pose)
                tseg = trunk[start : end + 1]
                tmax = float(np.nanmax(tseg)) if np.isfinite(tseg).any() else float("nan")
                biomech_v1["angles"]["trunk"] = {"max_deg": tmax}

                if np.isfinite(tmax) and tmax > params.max_trunk_angle_deg:
                    faults_v1.append(_fault(
                        "LUMBAR_FLEXION",
                        "warn",
                        tmax,
                        params.max_trunk_angle_deg,
                        f"trunk_angle_deg_max>{params.max_trunk_angle_deg}",
                    ))

        # Tempo faults (use inferred eccentric if inference happened)
"@

$src = [regex]::Replace($src, $patternBlock, $replacement, 1)
Write-Host "Patched: gated elbow faults + added trunk fault." -ForegroundColor Green

Set-Content -LiteralPath $File -Value $src -Encoding UTF8
Write-Host "Wrote: $File" -ForegroundColor Green

Select-String -Path $File -Pattern 'if ex in \("bench", "curl"\)|if ex in \("deadlift", "squat"\)|LUMBAR_FLEXION|max_trunk_angle_deg' | Select-Object -First 80
