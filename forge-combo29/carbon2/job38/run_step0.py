#!/usr/bin/env python3
"""
Job 38 Step 0 Runner (`run_step0.py`):
Verifies exe B (`/tmp/carbon2_job38/bld_base/forge`, commit 6b98f217, Release, g++ with libstdc++)
against the 4 fresh-process numbers (bench 11, bench 13, bench 16, go perft 5) and S14 on O and G.
Writes `builds.txt`, `step0_raw.txt`, `B_O_d12.nodes.txt` (+ `.meta`), `B_G_d12.nodes.txt` (+ `.meta`),
and appends the Step 0 completion line to `stamps.txt`.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from j38_harness import (
    BASE_COMMIT,
    EXP_BENCH11,
    EXP_BENCH13,
    EXP_BENCH16,
    EXP_G_SUM,
    EXP_O_FIRST3,
    EXP_O_SUM,
    EXP_PERFT5,
    FENS_G,
    FENS_O,
    OUT38,
    WORK38,
    check_four_numbers,
    fmt_pass,
    measure_depth_set,
    sha256_file,
    utc_now,
)


def main() -> None:
    exe_b = str(WORK38 / "bld_base/forge")
    exe_sha = sha256_file(exe_b)
    gxx_ver = subprocess.check_output(["g++", "--version"], text=True).splitlines()[0]
    cmake_ver = subprocess.check_output(["cmake", "--version"], text=True).splitlines()[0]

    nums = check_four_numbers(exe_b)
    o_nodes = measure_depth_set(exe_b, FENS_O, 12, [], OUT38 / "B_O_d12.nodes.txt")
    g_nodes = measure_depth_set(exe_b, FENS_G, 12, [], OUT38 / "B_G_d12.nodes.txt")

    checks = [
        fmt_pass("no-option bench 11 (fresh proc)", nums["bench11"], EXP_BENCH11),
        fmt_pass("no-option bench 13 (fresh proc)", nums["bench13"], EXP_BENCH13),
        fmt_pass("no-option bench 16 (fresh proc)", nums["bench16"], EXP_BENCH16),
        fmt_pass("no-option go perft 5 (fresh proc)", nums["perft5"], EXP_PERFT5),
        fmt_pass("S14 O (200 positions, depth 12) count", len(o_nodes), 200),
        fmt_pass("S14 O (200 positions, depth 12) sum", sum(o_nodes), EXP_O_SUM),
        fmt_pass("S14 O position 1 nodes", o_nodes[0], EXP_O_FIRST3[0]),
        fmt_pass("S14 O position 2 nodes", o_nodes[1], EXP_O_FIRST3[1]),
        fmt_pass("S14 O position 3 nodes", o_nodes[2], EXP_O_FIRST3[2]),
        fmt_pass("S14 G (353 positions, depth 12) count", len(g_nodes), 353),
        fmt_pass("S14 G (353 positions, depth 12) sum", sum(g_nodes), EXP_G_SUM),
    ]
    all_ok = all(ok for ok, _ in checks)
    ts = utc_now()

    raw_lines = [
        f"=== JOB 38 STEP 0: Base Commit {BASE_COMMIT} (exe B, Release, g++ with libstdc++) ===",
        f"Compiler : {gxx_ver}",
        f"CMake    : {cmake_ver}",
        f"exe B    : {exe_b} | sha256 = {exe_sha}",
        "",
        *[s for _, s in checks],
        "",
        f"STEP 0 OVERALL: {'PASS' if all_ok else 'FAIL'} ({int(all_ok)} == 1)",
        f"UTC finished: {ts}",
    ]
    (OUT38 / "step0_raw.txt").write_text("\n".join(raw_lines) + "\n", encoding="utf-8")

    builds_lines = [
        "=== JOB 38 BUILDS.TXT ===",
        f"Base commit: {BASE_COMMIT} (forge-combo29 subdirectory)",
        f"Compiler   : {gxx_ver} (libstdc++)",
        f"CMake      : {cmake_ver}",
        "Exact configure command: cmake -S <worktree>/forge-combo29 -B <build_dir> -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++",
        "Exact build command    : cmake --build <build_dir> -j4",
        "Exact g++ compile flags: /usr/bin/g++ -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_WEIGHTS=\"<worktree>/forge-combo29/src/nnue_weights.inc\" -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG -I<worktree>/forge-combo29/include -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4",
        "Exact g++ link flags   : /usr/bin/g++ -O3 -DNDEBUG <9 .cpp.o files> -o forge",
        "",
        f"0. exe B (base 6b98f217 as it is): {exe_b} | sha256={exe_sha}",
    ]
    (OUT38 / "builds.txt").write_text("\n".join(builds_lines) + "\n", encoding="utf-8")

    if not all_ok:
        raise SystemExit("STEP 0 FAILED!")

    with (OUT38 / "stamps.txt").open("a", encoding="utf-8") as sf:
        sf.write(f"{ts} | Step 0 finished (exe B sha256={exe_sha}; 4 numbers + S14 O=9500069 + S14 G=18466239 all PASS)\n")

    print("\n".join(raw_lines))


if __name__ == "__main__":
    main()
