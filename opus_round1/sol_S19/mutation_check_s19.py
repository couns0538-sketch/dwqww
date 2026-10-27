"""Planted-bug check for the S19 tool: every mutant must make the test suite fail; the unmutated copy must pass.

usage: python -I -B mutation_check_s19.py <new scratch dir>     (run with the NNUE venv python: numpy)
Copies the tool and the tests into <scratch>/<mutant>/, applies one source mutation to the tool copy and runs the
tests there. The files in this folder are never modified.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TOOL = "forge_sol_S19_wdl_scale_fit.py"
TESTS = "test_forge_sol_S19_wdl_scale_fit.py"
MUTANTS = {
    "stm_result_not_flipped": ("    stm_result = np.where(black, 1.0 - white_result, white_result)\n    return {\"score\": score,",
                               "    stm_result = white_result\n    return {\"score\": score,"),
    "queen_phase_3": ("PHASE_VALUE = (0, 0, 1, 1, 2, 4, 0)", "PHASE_VALUE = (0, 0, 1, 1, 2, 3, 0)"),
    "text_not_clipped": ("        scores.append(max(-TEXT_CLIP, min(TEXT_CLIP, score)))", "        scores.append(score)"),
    "table_always_fitted": ("        if entry[\"ci_excludes_reference\"]:\n            entry.update(k=entry[\"fitted_k\"]",
                            "        if entry[\"fitted_k\"] is not None:\n            entry.update(k=entry[\"fitted_k\"]"),
    "game_rule_ignores_result": ("pieces > prev[1] or result_text != prev[2]:", "pieces > prev[1]:"),
    "stride_ignored": ("    rows = list(range(0, n, 1 << 20))", "    stride = 1\n    rows = list(range(0, n, 1 << 20))"),
    "logloss_sign": ("    return float(np.mean(softplus - result * z))", "    return float(np.mean(softplus + result * z))"),
    "unseeded_bootstrap": ("    rng = np.random.default_rng(seed)\n    global_k", "    rng = np.random.default_rng()\n    global_k"),
}


def main(argv):
    scratch = Path(argv[0])
    scratch.mkdir()
    failures = 0
    for name in ["unmutated", *MUTANTS]:
        directory = scratch / name
        directory.mkdir()
        shutil.copy2(HERE / TOOL, directory / TOOL)
        shutil.copy2(HERE / TESTS, directory / TESTS)
        if name != "unmutated":
            old, new = MUTANTS[name]
            source = (directory / TOOL).read_text(encoding="utf-8")
            if source.count(old) != 1:
                print(f"{name}: mutation anchor not found exactly once")
                failures += 1
                continue
            (directory / TOOL).write_text(source.replace(old, new), encoding="utf-8", newline="\n")
        result = subprocess.run([sys.executable, "-I", "-B", str(directory / TESTS)], cwd=directory, env=dict(os.environ),
                                capture_output=True, text=True, check=False)
        last = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()][-1:]
        expected_fail = name != "unmutated"
        ok = (result.returncode != 0) if expected_fail else (result.returncode == 0)
        failures += not ok
        print(f"{name:28s} tests rc {result.returncode} ({last[0] if last else ''}) -> "
              f"{'CAUGHT' if expected_fail and ok else 'PASS' if ok else 'NOT CAUGHT' if expected_fail else 'FAIL'}")
    print("MUTATION CHECK:", "PASS" if not failures else f"FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
