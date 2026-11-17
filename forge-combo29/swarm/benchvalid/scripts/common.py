"""Shared paths for the benchvalid harness.

Every script here resolves its working root from $BENCHVALID_WORK (default
./benchvalid-work). Nothing is hard-coded to the machine this seat ran on, so a
reviewer can re-run the whole set from a clean checkout:

    export BENCHVALID_WORK=/tmp/bv
    git worktree add $BENCHVALID_WORK/base 6b98f217 --detach
    scripts/build_all.sh            # base build + probe binaries
    scripts/run_evidence.sh         # reproduces every file in evidence/
"""
from __future__ import annotations

import os
import pathlib

# Root that holds base/ (a worktree of 6b98f217), build/, bin/, mutants/, cov/.
WORK = pathlib.Path(os.environ.get("BENCHVALID_WORK", "./benchvalid-work")).resolve()
BASE_SRC = WORK / "base" / "forge-combo29"
BUILD = WORK / "build" / "forge"
BIN = WORK / "bin"
MUTANTS = WORK / "mutants"
COV = WORK / "cov"
SCRIPTS = pathlib.Path(__file__).resolve().parent

GCC = "/usr/bin/g++"
GCC_LIB = "/usr/lib/gcc/x86_64-linux-gnu/13"
MARCH = "x86-64-v4"

PINS = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}
