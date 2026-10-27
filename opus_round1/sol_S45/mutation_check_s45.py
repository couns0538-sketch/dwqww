#!/usr/bin/env python3
"""Planted-bug check for forge_sol_S45_rebase_ready.py: each mutant (one exact replacement, asserted unique) must make
test_forge_sol_S45_rebase_ready.py fail.

  python -I -B mutation_check_s45.py --work <new dir>
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "forge_sol_S45_rebase_ready.py"
TESTS = HERE / "test_forge_sol_S45_rebase_ready.py"

MUTANTS = [
    ("verdict_ignores_off_bench", 'if row.get("off_equals_base") is not True:', "if False:"),
    ("verdict_accepts_git_only", 'if not row.get("gnu_patch_dry_run"):', "if False:"),
    ("verdict_ignores_fma", 'elif b.get("fma") != 0:', "elif False:"),
    ("tunable_check_inverted", "return (not same), (f\"d{precheck_depth} ON", "return same, (f\"d{precheck_depth} ON"),
    ("node_exact_never_differs", "diff = [d for d in base_nodes if on_nodes.get(d) != base_nodes[d]]", "diff = []"),
    ("done_gates_not_detected", "if gid in done:", "if False:"),
    ("combine_policy_ignored", "elif combine:", "elif False:"),
    ("lock_sha_case_sensitive", "(lock_sha and opp_sha == lock_sha.upper())", "(lock_sha and opp_sha == lock_sha)"),
    ("gnu_patch_allows_fuzz", '[tool("patch"), "-p1", "-F0", "--dry-run"', '[tool("patch"), "-p1", "-F2", "--dry-run"'),
    ("net_change_not_checked", 'row["net_touched"] = md5_file(tree / "src" / "nnue_weights.inc") != net_md5',
     'row["net_touched"] = False'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work")
    a = ap.parse_args()
    work = Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix="s45_mut_"))
    work.mkdir(parents=True, exist_ok=True)
    src = TOOL.read_text(encoding="utf-8")
    base = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                          env=dict(os.environ, S45_TOOL=str(TOOL)))
    print(f"unmutated tool: tests {'PASS' if base.returncode == 0 else 'FAIL'}")
    if base.returncode != 0:
        print(base.stderr[-3000:])
        return 1
    caught = 0
    for name, old, new in MUTANTS:
        n = src.count(old)
        if n != 1:
            print(f"{name}: pattern occurs {n} times -> NOT APPLICABLE (counts as not caught)")
            continue
        mutant = work / f"s45_{name}.py"
        mutant.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(TESTS)], capture_output=True, text=True,
                           env=dict(os.environ, S45_TOOL=str(mutant)))
        failed = [ln.split(" (")[0] for ln in r.stderr.splitlines() if ln.startswith(("FAIL:", "ERROR:"))]
        ok = r.returncode != 0
        caught += ok
        print(f"{name}: {'CAUGHT' if ok else 'NOT CAUGHT'} ({len(failed)} failing: {', '.join(failed[:3])})")
    print(f"mutants caught {caught}/{len(MUTANTS)}")
    return 0 if caught == len(MUTANTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
