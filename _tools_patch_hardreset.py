from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()

def backup(p: Path) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = p.with_suffix(p.suffix + f".bak_{ts}")
    b.write_bytes(p.read_bytes())
    print(f"[backup] {b}")

def die(msg: str) -> None:
    raise SystemExit("PATCH FAIL: " + msg)

def ensure_contains(text: str, needle: str, name: str) -> None:
    if needle not in text:
        die(f"{name}: missing anchor: {needle}")

def insert_after_function(text: str, func_name: str, insert_text: str, name: str) -> str:
    # Find a top-level "def func_name(...):" and insert after its block by indentation.
    m = re.search(rf"(?m)^def\s+{re.escape(func_name)}\b[^\n]*\n", text)
    if not m:
        die(f"{name}: could not find def {func_name}()")

    start = m.start()
    # Find end of function block: next top-level def/class or EOF
    m2 = re.search(r"(?m)^(def|class)\s+", text[m.end():])
    end = (m.end() + m2.start()) if m2 else len(text)

    block = text[start:end]
    if insert_text.strip() in block:
        return text  # already there (paranoia)

    return text[:end] + "\n" + insert_text.rstrip() + "\n" + text[end:]

def replace_top_level_function(text: str, func_name: str, new_block: str, name: str) -> str:
    # Replace whole top-level function block.
    m = re.search(rf"(?m)^def\s+{re.escape(func_name)}\b[^\n]*\n", text)
    if not m:
        die(f"{name}: could not find def {func_name}()")

    # locate end at next top-level def/class or EOF
    m2 = re.search(r"(?m)^(def|class)\s+", text[m.end():])
    end = (m.end() + m2.start()) if m2 else len(text)
    return text[:m.start()] + new_block.rstrip() + "\n\n" + text[end:]

def ensure_exerciseparams_field(text: str, field_line: str, after_field_regex: str, name: str) -> str:
    if field_line.strip() in text:
        return text

    # Insert after a specific field (e.g., max_elbow_rom_asym_deg)
    m = re.search(after_field_regex, text, flags=re.M)
    if not m:
        die(f"{name}: could not find insertion point for ExerciseParams field")
    insert_at = m.end()
    return text[:insert_at] + "\n" + field_line.rstrip() + text[insert_at:]

def replace_between_markers(text: str, start_marker: str, end_marker: str, replacement_middle: str, name: str) -> str:
    s = text.find(start_marker)
    if s < 0:
        die(f"{name}: could not find start marker: {start_marker}")
    e = text.find(end_marker, s)
    if e < 0:
        die(f"{name}: could not find end marker: {end_marker}")

    # Keep the end marker line intact; replace from start_marker line up to just before end_marker
    # Move s to beginning of that line
    s_line = text.rfind("\n", 0, s) + 1
    e_line = text.rfind("\n", 0, e) + 1  # start of end_marker line
    return text[:s_line] + replacement_middle.rstrip() + "\n" + text[e_line:]

def patch_compute_rep_metrics() -> None:
    p = ROOT / "scripts" / "compute_rep_metrics.py"
    if not p.exists():
        die(f"missing file: {p}")
    backup(p)
    src = p.read_text(encoding="utf-8")

    name = "compute_rep_metrics.py"
    ensure_contains(src, "class ExerciseParams", name)
    ensure_contains(src, "def _driver_signal_from_elbow", name)
    ensure_contains(src, "def choose_best_signal", name)

    # 1) Ensure hip/knee landmark constants exist (simple insert after wrist constants block)
    if "L_HIP, R_HIP" not in src:
        # insert after the wrist line if present
        m = re.search(r"(?m)^L_WRIST,\s*R_WRIST\s*=\s*15,\s*16\s*$", src)
        if not m:
            die(f"{name}: could not find wrist landmark line to insert hips/knees")
        ins = "\nL_HIP, R_HIP = 23, 24\nL_KNEE, R_KNEE = 25, 26\n"
        src = src[:m.end()] + ins + src[m.end():]

    # 2) Ensure helper funcs exist (insert after _driver_signal_from_elbow block)
    helpers = r'''
def _nanfill_median(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    med = float(np.nanmedian(x)) if np.isfinite(x).any() else 0.0
    y = x.copy()
    y[~np.isfinite(y)] = med
    return y


def _normalize_robust_01(x: np.ndarray) -> np.ndarray:
    x = _nanfill_median(x)
    lo = float(np.percentile(x, 5))
    hi = float(np.percentile(x, 95))
    denom = max(1e-6, (hi - lo))
    z = (x - lo) / denom
    return np.clip(z, 0.0, 1.0).astype(float)


def _hip_y_series(pose: np.ndarray) -> np.ndarray:
    l_xy, _lv = _get_xyv(pose, L_HIP)
    r_xy, _rv = _get_xyv(pose, R_HIP)
    y = 0.5 * (l_xy[:, 1] + r_xy[:, 1])
    return y.astype(float)


def _driver_signal_from_hip_y(pose: np.ndarray) -> np.ndarray:
    y = _hip_y_series(pose)
    z = _normalize_robust_01(y)
    sig = 1.0 - z
    return sig.astype(float)


def _trunk_angle_deg_series(pose: np.ndarray) -> np.ndarray:
    ls, _ = _get_xyv(pose, L_SHOULDER)
    rs, _ = _get_xyv(pose, R_SHOULDER)
    lh, _ = _get_xyv(pose, L_HIP)
    rh, _ = _get_xyv(pose, R_HIP)

    sh = 0.5 * (ls + rs)
    hip = 0.5 * (lh + rh)
    v = sh - hip

    vert = np.array([0.0, -1.0], dtype=float)  # up in image coords
    ang = np.empty((pose.shape[0],), dtype=float)
    ang[:] = np.nan

    for t in range(pose.shape[0]):
        vt = v[t]
        nvt = np.linalg.norm(vt)
        if nvt < 1e-9:
            continue
        cosang = float(np.clip(np.dot(vt / nvt, vert), -1.0, 1.0))
        ang[t] = float(np.degrees(np.arccos(cosang)))
    return ang
'''.strip("\n")

    if "def _driver_signal_from_hip_y" not in src or "def _trunk_angle_deg_series" not in src:
        src = insert_after_function(src, "_driver_signal_from_elbow", helpers, name)

    # 3) Replace choose_best_signal to be exercise-aware (hard replace)
    new_choose = r'''
def choose_best_signal(pose: np.ndarray, exercise: str) -> Tuple[np.ndarray, str]:
    """
    Returns (signal, driver_label).
    Must be exercise-aware to prevent elbow-derived metrics leaking into deadlift/squat.
    """
    ex = (exercise or "").lower().strip()

    if pose is None or not isinstance(pose, np.ndarray) or pose.ndim != 3:
        return np.zeros((0,), dtype=float), "none"

    if ex in ("bench", "curl"):
        sig = _driver_signal_from_elbow(pose, side="L")
        return sig, "elbow_L"

    if ex in ("deadlift", "squat"):
        sig = _driver_signal_from_hip_y(pose)
        return sig, "hip_y"

    sig = _driver_signal_from_elbow(pose, side="L")
    return sig, "elbow_L"
'''.strip("\n")

    src = replace_top_level_function(src, "choose_best_signal", new_choose, name)

    # 4) Ensure ExerciseParams has max_trunk_angle_deg
    src = ensure_exerciseparams_field(
        src,
        "    max_trunk_angle_deg: float = 65.0  # placeholder; tune later",
        r"(?m)^\s+max_elbow_rom_asym_deg:\s*float\s*=\s*18\.0\s*$",
        name
    )

    # 5) Replace biomech/fault block between markers to gate elbow vs trunk
    start_marker = "# Phase2 biomech_v1:"
    end_marker = "# Tempo faults"
    replacement = r'''
        # Phase2 biomech_v1: exercise-aware biomechanics + faults
        biomech_v1: Dict[str, Any] = {"angles": {}}
        faults_v1: List[Dict[str, Any]] = []

        # --- Bench/Curl: elbow ROM + asym only
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
                        "PARTIAL_ROM_ELBOW", "warn",
                        dom_rom, params.min_elbow_rom_deg,
                        f"elbow_rom_deg<{params.min_elbow_rom_deg}",
                    ))

                if np.isfinite(romL) and np.isfinite(romR):
                    asym = float(abs(romL - romR))
                    if asym > params.max_elbow_rom_asym_deg:
                        faults_v1.append(_fault(
                            "ASYM_ROM_ELBOW", "info",
                            asym, params.max_elbow_rom_asym_deg,
                            f"|rom_L-rom_R|>{params.max_elbow_rom_asym_deg}",
                        ))

        # --- Deadlift/Squat: trunk angle proxy only (no elbow faults)
        if ex in ("deadlift", "squat"):
            if pose is not None and isinstance(pose, np.ndarray) and pose.ndim == 3 and pose.shape[1] >= 25:
                trunk = _trunk_angle_deg_series(pose)
                tseg = trunk[start : end + 1]
                tmax = float(np.nanmax(tseg)) if np.isfinite(tseg).any() else float("nan")
                biomech_v1["angles"]["trunk"] = {"max_deg": tmax}

                if np.isfinite(tmax) and tmax > params.max_trunk_angle_deg:
                    faults_v1.append(_fault(
                        "LUMBAR_FLEXION", "warn",
                        tmax, params.max_trunk_angle_deg,
                        f"trunk_angle_deg_max>{params.max_trunk_angle_deg}",
                    ))
'''.strip("\n")

    src = replace_between_markers(src, start_marker, end_marker, replacement, name)

    p.write_text(src, encoding="utf-8")
    print("[ok] patched scripts/compute_rep_metrics.py")

def patch_llm_wrapper() -> None:
    p = ROOT / "repright" / "llm_wrapper.py"
    if not p.exists():
        die(f"missing file: {p}")
    backup(p)
    src = p.read_text(encoding="utf-8")
    name = "llm_wrapper.py"

    ensure_contains(src, "Suggestions:", name)

    # Make suggestions conditional (stop unconditional “uneven” line)
    # Replace the three hard-coded suggestion lines with gated versions.
    src2 = src

    # Gate TEMPO line
    src2 = re.sub(
        r'(?m)^\s*lines\.append\("[- ]*Control the descent:.*"\)\s*$',
        '    if fast and int(fast) > 0:\n        lines.append("- Control the descent: aim ~0.5–1.0s down for consistency.")',
        src2,
        count=1
    )

    # Gate ASYM line
    src2 = re.sub(
        r'(?m)^\s*lines\.append\("[- ]*Left/right ROM looks uneven:.*"\)\s*$',
        '    if asym and int(asym) > 0:\n        lines.append("- Left/right ROM looks uneven: check grip symmetry and bar path; film from the front once.")',
        src2,
        count=1
    )

    # Keep the “goal” line always
    if src2 == src:
        # If regex didn’t match (file drift), do a safer minimal patch:
        # remove any unconditional uneven/tempo lines by commenting them out when counts are 0 is not feasible here.
        print("[warn] llm_wrapper.py patterns didn’t match exactly; open file and patch manually:")
        print("       - Ensure tempo + asym suggestion lines are inside if fast>0 / if asym>0 blocks.")
    else:
        p.write_text(src2, encoding="utf-8")
        print("[ok] patched repright/llm_wrapper.py")

def main():
    patch_compute_rep_metrics()
    patch_llm_wrapper()
    print("\nDONE. Now run your analyzer + coach again.\n")

if __name__ == "__main__":
    main()
