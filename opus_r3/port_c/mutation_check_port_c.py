#!/usr/bin/env python3
"""R3 port C planted-bug check: SA2's NnueInt16 mutants (opus_round1/sol_SA2/mutation_check_sa2.py) on the R3 stack,
built with the build switch FORGE_NNUE_INT16 and in either FORGE_NNUE_O2 state, plus one port-specific mutant.

Copies src/, include/ and tests/ of the worktree to <out>/<mutant>/ (read-only on the worktree), applies one textual
replacement (the anchor must occur exactly once), builds tests/nnue_int16_tests.cpp with MSYS2 g++ (the CMake CI
flags plus -DFORGE_NNUE_INT16=1 [-DFORGE_NNUE_O2=1]; AVX2 kernels, or -mno-avx2 for the scalar kernels) and runs it.
The unmutated control must PASS; every mutant must exit non-zero and print a "FAIL:" line.
  python -I -B mutation_check_port_c.py <worktree> <new out_dir> [--o2]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

GPP = r"C:\msys64\ucrt64\bin\g++.exe"
FLAGS = ["-std=c++20", "-O2", "-DNDEBUG", "-DFORGE_NNUE_HIDDEN=256", "-ffp-contract=off", "-fno-fast-math",
         "-march=x86-64-v3", "-mtune=znver5", "-static", "-DFORGE_NNUE_INT16=1"]
IDLE = 0x00000040
INC = "src/nnue_int16.inc"
MUTANTS = [  # (name, file, anchor, replacement, scalar build?)
    ("control (no mutation)", None, None, None, False),
    ("AVX2 output weights in natural order (packus lane order ignored)", INC,
     "constexpr std::array<int, 16> PackedOrder{0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7, 12, 13, 14, 15};",
     "constexpr std::array<int, 16> PackedOrder{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};", False),
    ("AVX2 incremental update always adds", INC,
     "value = dirty.changes[k].add ? _mm256_add_epi32(value, change) : _mm256_sub_epi32(value, change);",
     "value = _mm256_add_epi32(value, change);", False),
    ("AVX2 activation clamp at 4095", INC, "const __m256i top = _mm256_set1_epi16(ActivationScale);",
     "const __m256i top = _mm256_set1_epi16(ActivationScale - 1);", False),
    ("scalar square without rounding", INC, "    return (a * a + 1024) / 2048;", "    return (a * a) / 2048;", True),
    ("update follows the mode instead of the parent's tag", "src/nnue.cpp", "    if (parent.integer) {",
     "    if (int16_active()) {", False),
    # Port-specific: the float update path (AL1 loops or the O2 kernels) must clear the tag of a reused child.
    ("float update keeps a stale integer tag (hook's child.integer = false removed)", "src/nnue.cpp",
     "    child.integer = false;\n", "", False),
]


def main() -> int:
    tree, out = Path(sys.argv[1]), Path(sys.argv[2])
    o2 = "--o2" in sys.argv[3:]
    flags = FLAGS + (["-DFORGE_NNUE_O2=1"] if o2 else [])
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    env = {**os.environ, "PATH": r"C:\msys64\ucrt64\bin;" + os.environ["PATH"]}
    for k, (name, rel, anchor, repl, scalar) in enumerate(MUTANTS):
        d = out / f"m{k}"
        for sub in ("src", "include", "tests"):
            shutil.copytree(tree / sub, d / sub)
        if rel:
            text = (d / rel).read_bytes().decode("utf-8")
            assert text.count(anchor) == 1, f"{name}: anchor occurs {text.count(anchor)} times"
            (d / rel).write_bytes(text.replace(anchor, repl).encode("utf-8"))
        exe = d / "nnue_int16_tests.exe"
        cmd = [GPP, *flags, *(["-mno-avx2"] if scalar else []), "-I" + str(d / "include"), str(d / "tests" / "nnue_int16_tests.cpp"),
               str(d / "src" / "nnue.cpp"), str(d / "src" / "board.cpp"), str(d / "src" / "bitboard.cpp"), "-o", str(exe)]
        b = subprocess.run(cmd, capture_output=True, text=True, creationflags=IDLE, env=env)
        if b.returncode != 0:
            rows.append({"mutant": name, "build": "FAILED", "stderr": b.stderr[-1500:]})
            print(f"[{k}] {name}: BUILD FAILED", flush=True)
            continue
        r = subprocess.run([str(exe)], capture_output=True, text=True, creationflags=IDLE, timeout=600)
        fails = [line for line in r.stdout.splitlines() if line.startswith("FAIL:")]
        expected_fail = rel is not None
        caught = (r.returncode != 0 and bool(fails)) if expected_fail else (r.returncode == 0 and not fails)
        rows.append({"mutant": name, "file": rel, "scalar_build": scalar, "rc": r.returncode, "fail_lines": len(fails),
                     "first_fail": fails[0] if fails else None, "tail": r.stdout.splitlines()[-1] if r.stdout else "",
                     "result": "OK" if caught else "NOT CAUGHT"})
        print(f"[{k}] {name}: rc={r.returncode} FAIL lines={len(fails)} -> {'OK' if caught else 'NOT CAUGHT'}"
              + (f" | {fails[0][:150]}" if fails else f" | {rows[-1]['tail']}"), flush=True)
    ok = all(row.get("result") == "OK" for row in rows)
    (out / "mutation_result.json").write_bytes((json.dumps({"o2": o2, "flags": flags, "rows": rows, "pass": ok}, indent=1)
                                                + "\n").encode("utf-8"))
    print(f"FORGE_NNUE_O2={'1' if o2 else 'off'}: " + ("MUTATION CHECK PASS" if ok else "MUTATION CHECK FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
