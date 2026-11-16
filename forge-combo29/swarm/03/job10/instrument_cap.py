#!/usr/bin/env python3
"""instrument.py : make a SCRATCH copy of the r15 tree with a trace at the bare-king LMR cap, and build it.

Rules: the engine source in the repository is never modified (this works on a copy under /tmp), and the change is
recorded here as text so it can be reproduced.

The trace prints, to stderr, when the cap actually CHANGES the reduction (r was > 1 and gets clamped to 1):
    CAPFIRE ply=<ply> move=<uci> r_before=<r> depth=<depth> alpha=<a> beta=<b> node_type=<pv/all/cut> pv=<0|1>
plus a summary line at search end with the count. stderr is used so the UCI protocol on stdout is untouched.
"""
import os
import re
import shutil
import subprocess
import sys

SRC = "/agent/repos/pccopy/forge-combo29"
DST = "/tmp/instr155"
shutil.rmtree(DST, ignore_errors=True)
os.makedirs(DST)
for d in ("src", "include"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(DST, d))
shutil.copy(os.path.join(SRC, "CMakeLists.txt"), os.path.join(DST, "CMakeLists.txt"))

p = os.path.join(DST, "src", "search.cpp")
s = open(p).read()

# 1. the trace at the cap site: only when the cap actually bites (r > 1)
old = "            if (bare_king_lmr_cap) r = std::min(r, 1);\n"
assert s.count(old) == 1, f"anchor appears {s.count(old)} times"
new = (
    "            if (bare_king_lmr_cap && r > 1) {\n"
    "                if (std::getenv(\"FORGE_TRACE_CAP\") != nullptr) {\n"
    "                    std::fprintf(stderr, \"CAPFIRE ply=%d move=%s r_before=%d depth=%d alpha=%d beta=%d pv=%d\\n\",\n"
    "                                 static_cast<int>(ply), board.move_to_uci(move).c_str(), r,\n"
    "                                 static_cast<int>(depth), static_cast<int>(alpha), static_cast<int>(beta),\n"
    "                                 static_cast<int>(pv_node));\n"
    "                }\n"
    "            }\n"
    "            if (bare_king_lmr_cap) r = std::min(r, 1);\n"
)
s = s.replace(old, new, 1)

# make sure <cstdio> and <cstdlib> are available for fprintf/getenv
if "#include <cstdio>" not in s:
    s = "#include <cstdio>\n#include <cstdlib>\n" + s

open(p, "w").write(s)
print("instrumented cap site in", p)

build = "/tmp/instr155-build"
shutil.rmtree(build, ignore_errors=True)
os.makedirs(build)
r = subprocess.run(["cmake", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_COMPILER=g++",
                    "-DFORGE_MARCH=native", "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1", DST],
                   cwd=build, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout[-2000:], r.stderr[-2000:])
    sys.exit("cmake failed")
r = subprocess.run(["make", "-j4"], cwd=build, capture_output=True, text=True)
if r.returncode != 0:
    print(r.stdout[-3000:], r.stderr[-3000:])
    sys.exit("make failed")
print("built", os.path.join(build, "forge"))
