#!/usr/bin/env python3
"""S41 planted-bug check for the engine change: copy the tree, apply ONE exact replacement per mutant (asserting the
pattern occurs once), build only forge_net_scale_tests with CMake (JOBS=1, Idle), run it; every mutant must FAIL.

  python -I -B mutation_check_engine_s41.py --tree <worktree> --work <new dir under F:/opus_scratch/build/sol_S41>
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

CMAKE_FLAGS = "-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
TOOLS = "/d/grok-pc-data/dwqww/.claude/worktrees/b/tools/cmake_build_flags.sh"
IDLE = 0x00000040

MUTANTS = [
    ("apply_rounds_half_up", "include/forge/net_scale.hpp",
     "return static_cast<int>(static_cast<std::int64_t>(eval) * pct / 100);",
     "return static_cast<int>((static_cast<std::int64_t>(eval) * pct + 50) / 100);"),
    ("residual_path_not_scaled", "src/search.cpp",
     "return std::clamp(net_scale::apply(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, scale),",
     "return std::clamp(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network + 0 * scale,"),
    ("only_network_term_scaled", "src/search.cpp",
     "net_scale::apply(evaluator_.evaluate_runtime(board, ss->runtime_psqt) + network, scale)",
     "evaluator_.evaluate_runtime(board, ss->runtime_psqt) + net_scale::apply(network, scale)"),
    ("hce_only_path_scaled", "src/search.cpp",
     "if (!nnue::enabled || !nnue::available()) return evaluator_.evaluate(board);",
     "if (!nnue::enabled || !nnue::available()) return net_scale::apply(evaluator_.evaluate(board), net_scale::percent);"),
    ("default_not_off", "src/search.cpp", "int percent = Default;", "int percent = 99;"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--only")
    a = ap.parse_args()
    tree, work = Path(a.tree), Path(a.work)
    if work.exists():
        raise SystemExit("--work must be new")
    work.mkdir(parents=True)
    bash = shutil.which("bash") or r"C:\Program Files\Git\bin\bash.exe"
    results = []
    for name, rel, old, new in MUTANTS:
        if a.only and name != a.only:
            continue
        src = work / name / "src_tree"
        for part in ("src", "include", "tests", "bench", "tools"):
            shutil.copytree(tree / part, src / part)
        shutil.copyfile(tree / "CMakeLists.txt", src / "CMakeLists.txt")
        f = src / rel
        text = f.read_text(encoding="utf-8")
        n = text.count(old)
        if n != 1:
            print(f"{name}: pattern occurs {n} times in {rel} -> NOT APPLICABLE", flush=True)
            results.append((name, "NOT_APPLICABLE"))
            continue
        f.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
        bd = work / name / "build"
        env = dict(os.environ, JOBS="1")
        b = subprocess.run([bash, TOOLS, src.as_posix(), bd.as_posix(), CMAKE_FLAGS, "forge_net_scale_tests"],
                           capture_output=True, text=True, env=env, creationflags=IDLE)
        if b.returncode != 0:
            print(f"{name}: BUILD FAILED (counts as caught only if intended; here: error)\n{b.stdout[-1500:]}{b.stderr[-1500:]}", flush=True)
            results.append((name, "BUILD_FAILED"))
            continue
        exe = bd / "forge_net_scale_tests.exe"
        r = subprocess.run([str(exe)], capture_output=True, text=True, creationflags=IDLE, timeout=900)
        fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL ")]
        summary = [l for l in r.stdout.splitlines() if l.startswith("SUMMARY")]
        verdict = "CAUGHT" if r.returncode != 0 else "NOT CAUGHT"
        print(f"{name}: {verdict} exit {r.returncode} {summary[0] if summary else ''} first: {fails[0] if fails else '-'}", flush=True)
        results.append((name, verdict))
    caught = sum(1 for _, v in results if v == "CAUGHT")
    print(f"engine mutants caught {caught}/{len(results)}")
    return 0 if caught == len(results) and results else 1


if __name__ == "__main__":
    sys.exit(main())
