#!/usr/bin/env python3
"""NEGATIVE CONTROL for check_02f2.py — proves the hardened checker cannot confirm on a missing line.

Seat 19's warning: a parser that finds no line can produce a NaN/None and still print CONFIRMS.  This control
feeds the verdict logic a recorded result set in which the `info string searchmoves ...` line is STRIPPED, and
requires the checker's assertions to fail.  If this control ever prints CONFIRMS, the checker is broken.

Method: run check_02f2.py normally (which must CONFIRMS), then run it again against a doctored copy of an engine
that still answers `bestmove 0000` but never prints the searchmoves info line.  The doctoring is a one-line
text change on a scratch copy OUTSIDE the repo (printf-wrapped exe is not enough: the engine must be the one
that answers), so the second run must exit 2 with INCONCLUSIVE.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SW = os.path.dirname(HERE)
SRC = "/agent/repos/base/forge-combo29"
SCRATCH = os.path.expanduser("~/work/noinfo")
EXE_REAL = os.path.join(SRC, "build-rel", "forge")
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"

print("=== control 0: the real checker on the real build (must CONFIRMS, exit 0) ===")
p0 = subprocess.run([sys.executable, os.path.join(HERE, "check_02f2.py"), "--exe", EXE_REAL,
                     "--fen", FEN, "--out", "/tmp/ctl_real"], capture_output=True, text=True)
print("exit:", p0.returncode)
print([l for l in p0.stdout.splitlines() if l.startswith("VERDICT")])

print()
print("=== control 1: same checker, engine with the searchmoves info line REMOVED (must be INCONCLUSIVE, exit 2) ===")
if not os.path.isdir(SCRATCH):
    shutil.copytree(SRC, SCRATCH, ignore=shutil.ignore_patterns("build-*", "tests_*", "*.zip"))
uci = os.path.join(SCRATCH, "src", "search.cpp")
src = open(uci).read()
needle = 'info string searchmoves restriction has no legal root moves'
hits = src.count(needle)
print(f"occurrences of the quoted line in {uci}: {hits}")
src = src.replace(needle, 'XXnothing matches the quoted sentence XX')
open(uci, "w").write(src)
print("doctor: replaced the whole printed sentence with a sentence that contains none of it")
env = dict(os.environ, CC="/usr/bin/gcc-13", CXX="/usr/bin/g++-13")
b = subprocess.run(["cmake", "-S", SCRATCH, "-B", os.path.join(SCRATCH, "build-noinfo"),
                    "-DCMAKE_BUILD_TYPE=Release"], capture_output=True, text=True, env=env)
b2 = subprocess.run(["cmake", "--build", os.path.join(SCRATCH, "build-noinfo"), "-j4"],
                    capture_output=True, text=True, env=env)
print("build exit:", b2.returncode)
if b2.returncode != 0:
    print(b2.stdout[-2000:], b2.stderr[-2000:]); sys.exit(3)
EXE_DOC = os.path.join(SCRATCH, "build-noinfo", "forge")
p1 = subprocess.run([sys.executable, os.path.join(HERE, "check_02f2.py"), "--exe", EXE_DOC,
                     "--fen", FEN, "--out", "/tmp/ctl_doctored"], capture_output=True, text=True)
print("exit:", p1.returncode)
for l in p1.stdout.splitlines():
    if l.startswith("VERDICT") or l.strip().startswith("!"):
        print(l)
ok = (p0.returncode == 0 and "CONFIRMS" in p0.stdout and p1.returncode == 2
      and "INCONCLUSIVE" in p1.stdout and "CONFIRMS" not in p1.stdout)
print()
print("CONTROL RESULT:", "PASS — a missing quoted line cannot pass as a CONFIRMS" if ok
      else "FAIL — the checker can still confirm without the line")
sys.exit(0 if ok else 4)
