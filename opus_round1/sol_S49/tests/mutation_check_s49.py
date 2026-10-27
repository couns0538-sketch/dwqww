#!/usr/bin/env python3
"""Planted-bug check for pc_speed_ci_20261027.ps1: each mutant (one exact replacement, asserted unique) must make
tests/test_pc_speed_ci.py fail. Mutants only weaken selection / refusal / statistics logic; none adds an affinity or
priority write, and the tests run only -SelfTest and -PlanOnly (no engine, no pinning).

  python -I -B tests/mutation_check_s49.py --work <new dir>
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "pc_speed_ci_20261027.ps1"
TESTS = HERE / "test_pc_speed_ci.py"

MUTANTS = [
    ("select_ignores_gate_cores", "foreach ($c in $Used) { [void]$blocked.Add($c) }", "foreach ($c in @()) { [void]$blocked.Add($c) }"),
    ("select_ignores_reserved", "foreach ($c in $Reserved) { [void]$blocked.Add($c) }", "foreach ($c in @()) { [void]$blocked.Add($c) }"),
    ("requested_core_not_checked", "if ($free -contains $Requested) {", "if ($true) {"),
    ("live_gate_scan_dropped", "$used = @(@($live.Cores) + @($runInfo) + @($manifestCores) | Sort-Object -Unique)",
     "$used = @(@($runInfo) + @($manifestCores) | Sort-Object -Unique)"),
    ("manifest_cores_dropped", "$used = @(@($live.Cores) + @($runInfo) + @($manifestCores) | Sort-Object -Unique)",
     "$used = @(@($live.Cores) + @($runInfo) | Sort-Object -Unique)"),
    ("runinfo_age_filter_dropped", "if ((Get-Item -LiteralPath $ri).LastWriteTime -lt $cut) { continue }", "$null = $cut"),
    ("boxonly_refusal_dropped", "if ($BoxOnly -and ($live.GateProcesses -gt 0 -or $runInfo.Count -gt 0)) {", "if ($false) {"),
    ("protected_outdir_allowed", "if (-not (Test-OutDirAllowed $OutDir)) {", "if ($false) {"),
    ("cores_0_3_rule_dropped", "foreach ($c in 0, 1, 2, 3) { if ($ReservedCores -notcontains $c)", "foreach ($c in @()) { if ($ReservedCores -notcontains $c)"),
    ("abba_alternation_broken", "$first, $second = if ($i % 2 -eq 0) { 'A', 'B' } else { 'B', 'A' }", "$first, $second = 'A', 'B'"),
    ("bootstrap_lower_bound_wrong", "$lo = $meds[[int][Math]::Floor(0.025 * ($Reps - 1))]", "$lo = $meds[[int][Math]::Floor(0.975 * ($Reps - 1))]"),
    ("refusal_does_not_exit", "if ($sel.Core -lt 0) { exit 3 }", "if ($sel.Core -lt 0) { }"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work")
    a = ap.parse_args()
    work = Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix="s49_mut_"))
    work.mkdir(parents=True, exist_ok=True)
    src = SCRIPT.read_text(encoding="utf-8")
    base = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                          env=dict(os.environ, PS49_SCRIPT=str(SCRIPT)))
    print(f"unmutated script: tests {'PASS' if base.returncode == 0 else 'FAIL'}", flush=True)
    if base.returncode != 0:
        print(base.stderr[-3000:])
        return 1
    caught = 0
    for name, old, new in MUTANTS:
        n = src.count(old)
        if n != 1:
            print(f"{name}: pattern occurs {n} times -> NOT APPLICABLE (counts as not caught)", flush=True)
            continue
        mdir = work / name
        mdir.mkdir()
        mutant = mdir / "pc_speed_ci_20261027.ps1"
        mutant.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                           env=dict(os.environ, PS49_SCRIPT=str(mutant)))
        failed = [ln.split(" (")[0] for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{name}: {'CAUGHT' if ok else 'NOT CAUGHT'} ({len(failed)} failing: {', '.join(failed[:3])})", flush=True)
    print(f"mutants caught {caught}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
