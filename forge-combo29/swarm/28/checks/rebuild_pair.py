#!/usr/bin/env python3
"""rebuild_pair.sh equivalent — build the same source TWICE with separate object files, then A/B them.

Seat 19's 19-F7 measured "build-to-build spread of ONE source" at 4.2 %. My first attempt produced two
BYTE-IDENTICAL binaries (sha256 equal), so its A/B only measured run-to-run noise (0.33 %) and says
nothing about build-to-build variance. A build difference can only exist if the binaries differ, so the
honest check must (1) produce two builds that may differ and (2) confirm whether they do differ.

This script: full `cmake` configure + `make` from a CLEAN directory for each of A and B (separate
object files, separate CMake cache, same source, same flags, same compiler), reports the sha256 of each
exe, then runs the same A/B bench harness.

Usage: rebuild_pair.sh OUTROOT ROUNDS
"""
import hashlib
import os
import shutil
import subprocess
import sys

SRC = "/agent/repos/base/forge-combo29"
FLAGS = ["-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=/usr/bin/g++-13"]


def build(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)
    subprocess.run(["cmake", SRC] + FLAGS, cwd=path, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    subprocess.run(["make", "-j4"], cwd=path, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    exe = os.path.join(path, "forge")
    return exe, hashlib.sha256(open(exe, "rb").read()).hexdigest()


def main() -> int:
    root, rounds = sys.argv[1], sys.argv[2]
    os.makedirs(root, exist_ok=True)
    exes = {}
    for name in ("A", "B"):
        exe, sha = build(os.path.join(root, "build" + name))
        exes[name] = exe
        print(f"{name}: {sha}  {exe}")
    same = hashlib.sha256(open(exes["A"], "rb").read()).hexdigest() == \
        hashlib.sha256(open(exes["B"], "rb").read()).hexdigest()
    print(f"binaries byte-identical: {same}")
    subprocess.run(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ab_bench.py"),
                    exes["A"], exes["B"], rounds, os.path.join(root, "ab")], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
