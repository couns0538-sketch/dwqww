#!/usr/bin/env python3
"""R3-6 planted bugs for UCI SmpHelpersPastDepth: each mutant is a fresh copy of src/include/tests
with ONE replacement in src/search/iterative.inc (asserted to occur once); tests/smp_tests.cpp is
built against it with MSYS2 g++ (forge_core sources, -O2, static) and run. A mutant is "killed"
when forge_smp_tests fails. The unmutated copy is built and run the same way as the control.

With --repeat N every test binary runs N times (the control must pass every run; a mutant whose
effect depends on where a search is stopped is reported with its kill rate).

--only control --repeat 0 --opt=-O3 just builds the unmutated test binary (e.g. of another tree, for
an interleaved comparison).

usage: mutation_check.py <tree> <scratch_dir> [--only NAME] [--repeat N] [--opt=-O3]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

GPP = "C:/msys64/ucrt64/bin/g++.exe"
CORE = ["src/bitboard.cpp", "src/board.cpp", "src/book.cpp", "src/eval.cpp", "src/eval_params.cpp", "src/nnue.cpp",
        "src/search.cpp"]
IT = "src/search/iterative.inc"
MUTANTS = [
    ("control", None, None),
    ("M1_helpers_stop_at_limit",
     "const int last_depth = options::smp_helpers_past_depth && !is_main() && mate_moves == 0 ? 64 : max_depth;",
     "const int last_depth = max_depth;"),
    ("M2_result_not_capped",
     "        if (depth > max_depth) continue;\n",
     ""),
    ("M3_partial_deeper_iteration_replaces_move",
     "if (depth <= max_depth && ss->pv_length > 0 &&",
     "if (ss->pv_length > 0 &&"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree")
    ap.add_argument("scratch")
    ap.add_argument("--only", default="")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--opt", default="-O2", help="optimisation flag (CMake Release uses -O3)")
    a = ap.parse_args()
    tree, scratch = Path(a.tree), Path(a.scratch)
    env = dict(os.environ)
    env["PATH"] = "C:/msys64/ucrt64/bin;" + env.get("PATH", "")
    results = []
    for name, old, new in MUTANTS:
        if a.only and name != a.only:
            continue
        out = scratch / name
        if out.exists():
            raise SystemExit(f"{out} exists: use a fresh scratch folder")
        out.mkdir(parents=True)
        for sub in ("src", "include", "tests"):
            shutil.copytree(tree / sub, out / sub)
        if old is not None:
            path = out / IT
            text = path.read_bytes().decode("utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{name}: pattern found {text.count(old)} times")
            path.write_bytes(text.replace(old, new).encode("utf-8"))
        exe = out / "forge_smp_tests.exe"
        t0 = time.time()
        cmd = [GPP, "-std=c++20", a.opt, "-DNDEBUG", "-march=x86-64-v3", "-mtune=znver5", "-fno-fast-math",
               "-ffp-contract=off", "-DFORGE_NNUE_HIDDEN=256", "-static", "-pthread", "-Iinclude",
               "tests/smp_tests.cpp"] + CORE + ["-o", str(exe)]
        b = subprocess.run(cmd, cwd=out, capture_output=True, text=True, env=env)
        (out / "build.log").write_text(b.stdout + b.stderr, encoding="utf-8")
        if b.returncode != 0:
            print(f"{name}: BUILD FAILED (see {out / 'build.log'})", flush=True)
            results.append((name, "build failed", ""))
            continue
        failed_runs = 0
        all_fails = []
        for rep in range(a.repeat):
            r = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, timeout=1800)
            (out / f"run{rep}.log").write_text(r.stdout + r.stderr, encoding="utf-8")
            fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL")]
            failed_runs += 1 if r.returncode != 0 else 0
            all_fails += fails
            print(f"{name} run {rep}: forge_smp_tests {'PASS' if r.returncode == 0 else 'FAIL'} "
                  f"(exit {r.returncode}, {len(fails)} FAIL lines, {time.time() - t0:.0f} s)", flush=True)
            for l in fails[:6]:
                print("    " + l, flush=True)
        verdict = "PASS" if failed_runs == 0 else "FAIL"
        results.append((name, verdict, f"{failed_runs}/{a.repeat} runs failed"))
    print("\nsummary:")
    for name, verdict, rate in results:
        expect = "PASS" if name == "control" else "FAIL"
        status = "ok" if verdict == expect else ("SURVIVED" if name != "control" else "CONTROL BROKEN")
        print(f"  {name}: {verdict}, {rate} ({'killed' if name != 'control' and verdict == 'FAIL' else status})")


if __name__ == "__main__":
    main()
