#!/usr/bin/env python3
"""make_reverse_patch.py OUT.patch.txt : build the reverse-test tree in a SCRATCH copy and emit a text patch.

The reverse test of job 6 needs the BASE tree (6b98f217) with the r15 build's two bare-king rules turned ON. The base
tree does not contain them at all (it has no `root_bare_king_` member), so this is not a matter of flipping macros:
the logic has to be ported. Per the rules a change to the engine is only ever a TEXT PATCH, never source in the
repository — so this script writes a unified diff (`.patch.txt`) against 6b98f217 and nothing else is committed.

The port is the minimal equivalent of r15's code (verified by reading src/search.cpp:1902-1921 and :2477 of the r15
tree):
  * member `bool root_bare_king_` in Worker;
  * set at the root: either side's occupancy equals exactly its king;
  * `bare_king_mode` becomes `bare_king_rule && (a side has a lone king)` with
    `bare_king_rule = multi_worker || root_bare_king_`   (r15's FORGE_FIX_BARE_KING_ONE_THREAD)
  * `bare_king_lmr_cap = !bare_king_mode && root_bare_king_ && (a side has a lone king)`, applied as
    `r = std::min(r, 1)` at the late-move-reduction site   (r15's FORGE_FIX_BARE_KING_LMR_CAP)
Both switches default to 1 here, because the test needs them ON.
"""
import os
import shutil
import subprocess
import sys

OUT = sys.argv[1]
SCRATCH = "/tmp/rev6"
BASE = "/agent/repos/base/forge-combo29"

shutil.rmtree(SCRATCH, ignore_errors=True)
os.makedirs(SCRATCH)
# pristine copies of the two files we touch, and of the originals for diffing
for rel in ("src/search.cpp", "include/forge/search.hpp"):
    dst = os.path.join(SCRATCH, "new", rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(os.path.join(BASE, rel), dst)
    dst0 = os.path.join(SCRATCH, "orig", rel)
    os.makedirs(os.path.dirname(dst0), exist_ok=True)
    shutil.copy(os.path.join(BASE, rel), dst0)

# ---- search.hpp: add the member
p = os.path.join(SCRATCH, "new", "include/forge/search.hpp")
lines = open(p).read().splitlines(keepends=True)
out, done = [], False
for l in lines:
    out.append(l)
    if not done and "bool root_restricted_ = false;" in l:
        out.append("    // job6 reverse test: one side of the ROOT position has only its king (r15's root_bare_king_)\n")
        out.append("    bool root_bare_king_ = false;\n")
        done = True
if not done:
    sys.exit("FAIL: root_restricted_ not found in search.hpp")
open(p, "w").writelines(out)

# ---- search.cpp
p = os.path.join(SCRATCH, "new", "src/search.cpp")
src = open(p).read()

# sanity: this is the base tree, so these markers must be absent
for absent in ("root_bare_king_", "bare_king_lmr_cap", "FORGE_FIX_BARE_KING_"):
    if absent in src:
        sys.exit(f"FAIL: {absent} already present — this is not the pristine base file")

old = (
    "#if FORGE_BARE_KING_MATE_FIX\n"
    "    const bool multi_worker = all_workers_ != nullptr && all_workers_->size() > 1;\n"
    "    const bool bare_king_mode = multi_worker &&\n"
    "        (board.occupied(White) == board.pieces(White, King) ||\n"
    "         board.occupied(Black) == board.pieces(Black, King));\n"
    "#else\n"
    "    constexpr bool bare_king_mode = false;\n"
    "#endif\n"
)
new = (
    "// job6 reverse test: the r15 PC build's two bare-king rules, as switches.\n"
    "#ifndef FORGE_FIX_BARE_KING_LMR_CAP\n"
    "#define FORGE_FIX_BARE_KING_LMR_CAP 1\n"
    "#endif\n"
    "#ifndef FORGE_FIX_BARE_KING_ONE_THREAD\n"
    "#define FORGE_FIX_BARE_KING_ONE_THREAD 1\n"
    "#endif\n"
    "#if FORGE_BARE_KING_MATE_FIX\n"
    "    const bool multi_worker = all_workers_ != nullptr && all_workers_->size() > 1;\n"
    "#if FORGE_FIX_BARE_KING_ONE_THREAD\n"
    "    const bool bare_king_rule = multi_worker || root_bare_king_;\n"
    "#else\n"
    "    const bool bare_king_rule = multi_worker;\n"
    "#endif\n"
    "    const bool bare_king_mode = bare_king_rule &&\n"
    "        (board.occupied(White) == board.pieces(White, King) ||\n"
    "         board.occupied(Black) == board.pieces(Black, King));\n"
    "#else\n"
    "    constexpr bool bare_king_mode = false;\n"
    "#endif\n"
    "#if FORGE_FIX_BARE_KING_LMR_CAP\n"
    "    const bool bare_king_lmr_cap = !bare_king_mode && root_bare_king_ &&\n"
    "        (board.occupied(White) == board.pieces(White, King) ||\n"
    "         board.occupied(Black) == board.pieces(Black, King));\n"
    "#else\n"
    "    constexpr bool bare_king_lmr_cap = false;\n"
    "#endif\n"
)
if old not in src:
    sys.exit("FAIL: the base bare_king_mode block is not in the expected form")
src = src.replace(old, new, 1)

# root assignment
marker = "    root_restricted_ = limits.search_moves_specified;\n"
if marker not in src:
    sys.exit("FAIL: root_restricted_ assignment not found")
src = src.replace(
    marker,
    marker + ("    root_bare_king_ = board.occupied(White) == board.pieces(White, King) ||\n"
              "                      board.occupied(Black) == board.pieces(Black, King);\n"),
    1,
)

# the LMR cap site: in r15 the cap sits immediately before `const int reduced_depth = std::clamp(new_depth - r, ...)`,
# right after the LmrLateParentRelief line. Anchor on that exact pair, and refuse if it is not unique.
anchor = "            if (tune::LmrLateParentRelief && ss->arrival_index >= 7 && move_count <= 4) --r;\n"
count = src.count(anchor)
if count != 1:
    sys.exit(f"FAIL: the LMR anchor appears {count} times (expected exactly 1) — refusing to guess")
src = src.replace(anchor, anchor + "            if (bare_king_lmr_cap) r = std::min(r, 1);\n", 1)
open(p, "w").write(src)

# ---- emit the unified diff
with open(OUT, "w") as f:
    for rel in ("include/forge/search.hpp", "src/search.cpp"):
        r = subprocess.run(["diff", "-u",
                            "--label", f"a/{rel}", "--label", f"b/{rel}",
                            os.path.join(SCRATCH, "orig", rel),
                            os.path.join(SCRATCH, "new", rel)],
                           capture_output=True, text=True)
        f.write(r.stdout)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
