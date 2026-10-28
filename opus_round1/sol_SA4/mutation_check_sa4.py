#!/usr/bin/env python3
"""S-A4 planted-bug check: width bugs that the H256 build cannot see must make the H512 test FAIL.

Builds tests/nnue_gen_net.cpp, generates the CTest H512 net (512 units, seed 20261027), then for each mutant copies src/,
include/ and tests/ of the worktree to <out>/<mutant>/ (read-only on the worktree), applies one textual replacement (the
anchor must occur exactly once) and builds tests/nnue_int16_tests.cpp with MSYS2 g++ (CMake CI flags, AVX2 kernels):
  - at H512 (-UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=<generated net>): must FAIL (or not build);
  - at H256 (the lock net): reported, expected to PASS for the width bugs (why the H512 target exists).
The unmutated control must PASS at both widths.
  python -I -B mutation_check_sa4.py <worktree> <out_dir>
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
         "-march=x86-64-v3", "-mtune=znver5", "-static"]
IDLE = 0x00000040
INC = "src/nnue_int16.inc"
MUTANTS = [  # (name, file, anchor, replacement)
    ("control (no mutation)", None, None, None),
    ("AVX2 incremental update stops at unit 256", INC, "        for (int h = 0; h < HiddenSize; h += 8) {",
     "        for (int h = 0; h < 256; h += 8) {"),
    ("AVX2 integer output stops at unit 256", INC, "    for (int h = 0; h < HiddenSize; h += 16) {",
     "    for (int h = 0; h < 256; h += 16) {"),
    ("opponent output weights at a fixed offset 256", INC, "w.packed_w2.data() + HiddenSize + h", "w.packed_w2.data() + 256 + h"),
    ("FORGE_NNUE_WEIGHTS ignored", "src/nnue.cpp", "#if defined(FORGE_NNUE_WEIGHTS)\n#include FORGE_NNUE_WEIGHTS",
     "#if 0\n#include FORGE_NNUE_WEIGHTS"),
]
ENV = {**os.environ, "PATH": r"C:\msys64\ucrt64\bin;" + os.environ["PATH"]}


def build(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, creationflags=IDLE, env=ENV)


def main() -> int:
    tree, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    gen = out / "nnue_gen_net.exe"
    b = build([GPP, "-std=c++20", "-O2", "-static", str(tree / "tests" / "nnue_gen_net.cpp"), "-o", str(gen)])
    assert b.returncode == 0, b.stderr
    net = out / "nnue_test_h512.inc"
    assert subprocess.run([str(gen), "512", "20261027", str(net)], creationflags=IDLE).returncode == 0
    print(f"generated {net.name}: {net.stat().st_size} bytes", flush=True)
    rows = []
    for k, (name, rel, anchor, repl) in enumerate(MUTANTS):
        d = out / f"m{k}"
        for sub in ("src", "include", "tests"):
            shutil.copytree(tree / sub, d / sub)
        if rel:
            text = (d / rel).read_text(encoding="utf-8")
            assert text.count(anchor) == 1, f"{name}: anchor occurs {text.count(anchor)} times"
            (d / rel).write_text(text.replace(anchor, repl), encoding="utf-8", newline="\n")
        row = {"mutant": name, "file": rel}
        for width, extra in (("H512", ["-UFORGE_NNUE_HIDDEN", "-DFORGE_NNUE_HIDDEN=512", f'-DFORGE_NNUE_WEIGHTS="{net.as_posix()}"']),
                             ("H256", [])):
            exe = d / f"nnue_int16_tests_{width}.exe"
            cmd = [GPP, *FLAGS, *extra, "-I" + str(d / "include"), str(d / "tests" / "nnue_int16_tests.cpp"),
                   str(d / "src" / "nnue.cpp"), str(d / "src" / "board.cpp"), str(d / "src" / "bitboard.cpp"), "-o", str(exe)]
            b = build(cmd)
            if b.returncode != 0:
                first = next((x for x in b.stderr.splitlines() if "error" in x), b.stderr[-300:])
                row[width] = {"build": "FAILED", "error": first[:300]}
                continue
            r = subprocess.run([str(exe)], capture_output=True, text=True, creationflags=IDLE, timeout=900)
            fails = [x for x in r.stdout.splitlines() if x.startswith("FAIL:")]
            row[width] = {"rc": r.returncode, "fail_lines": len(fails), "first_fail": fails[0][:200] if fails else None,
                          "tail": (r.stdout.splitlines() or [""])[-1]}
        h512, h256 = row["H512"], row["H256"]
        if rel is None:
            ok = h512.get("rc") == 0 and h256.get("rc") == 0
        else:
            ok = h512.get("build") == "FAILED" or (h512.get("rc", 0) != 0 and h512.get("fail_lines", 0) > 0)
        row["result"] = "OK" if ok else ("NOT CAUGHT" if rel else "CONTROL FAILED")
        rows.append(row)
        print(f"[{k}] {name}: H512 {h512.get('build') or ('rc=' + str(h512.get('rc')))} "
              f"{(h512.get('first_fail') or h512.get('error') or h512.get('tail') or '')[:140]} | H256 "
              f"{h256.get('build') or ('rc=' + str(h256.get('rc')))} {(h256.get('first_fail') or h256.get('tail') or '')[:60]} -> {row['result']}",
              flush=True)
    ok = all(r["result"] == "OK" for r in rows)
    (out / "mutation_result.json").write_text(json.dumps({"rows": rows, "pass": ok}, indent=1) + "\n", encoding="utf-8")
    print("MUTATION CHECK PASS" if ok else "MUTATION CHECK FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
