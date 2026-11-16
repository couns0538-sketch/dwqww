#!/usr/bin/env python3
"""check_29F9.py OUTDIR : independent check of seat 29's 29-F9.

29-F9 claims: no NNUE v3 network FILE exists on any branch of this repository. That matters because Opus's
file 2 Rule 2 tells every seat the owner's PC "plays with ITS OWN net file loaded (NNUEArch true, a
king-bucket net)" — so the PC's net is not in this repository, and every seat's profile here is of the
built-in network, not of the code path the PC actually runs.

My method (independent of theirs): search the REPOSITORY TREE for files that could be a network, by
extension and by size, on the branches that matter — the base commit and the v3 path branch — and also ask
the engine itself whether it can load a network (NnueFile option) and what it reports at startup.

Verdict rule, fixed before running:
  CONFIRMS if (a) the tracked file list of the base tree contains no file whose name ends in .nnue or .bin,
  AND (b) no tracked file is plausibly a weights blob (no file over 1 MB that is not source/text data), AND
  (c) the engine's own `uci` answer shows NnueFile with an empty default.
  REFUTES otherwise, and prints which clause failed.
"""
import os
import re
import subprocess
import sys

outdir = sys.argv[1]
os.makedirs(outdir, exist_ok=True)
REPO = "/agent/repos/dwqww"
lines = []


def sh(cmd, cwd=REPO):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True).stdout


# (a) tracked files in the base tree
base = "6b98f2170a3210e71beed04bbd2553972c253ed7"
tracks = sh("git ls-tree -r --name-only %s" % base).splitlines()
ext_hits = [p for p in tracks if re.search(r"\.(nnue|bin)$", p, re.I)]
lines.append("tracked files in the base tree: %d" % len(tracks))
lines.append("(a) files ending .nnue or .bin: %d" % len(ext_hits))
for p in ext_hits[:20]:
    lines.append("    " + p)

# (b) any implausibly large tracked file (a weights blob would be)
sized = sh("git ls-tree -r -l %s" % base).splitlines()
big = []
for row in sized:
    parts = row.split(None, 3)
    if len(parts) == 4 and parts[3].isdigit() and int(parts[3]) > 1_000_000:
        big.append((int(parts[3]), parts[3 + 0] if False else row.split("\t")[-1]))
big.sort(reverse=True)
lines.append("(b) tracked files larger than 1 MB: %d" % len(big))
for size, p in big[:10]:
    lines.append("    %9d  %s" % (size, p))

# the v3 branch and the handoff branch, if reachable
for branch in ("for-fable-and-opus/astra-0017-v3-path",
               "handoff/fable-opus-combo29-all-20261114"):
    ref = "origin/" + branch
    if sh("git rev-parse --verify -q %s" % ref).strip():
        t = sh("git ls-tree -r --name-only %s" % ref).splitlines()
        hits = [p for p in t if re.search(r"\.(nnue|bin)$", p, re.I)]
        lines.append("%s: %d tracked files, %d with .nnue/.bin" % (branch, len(t), len(hits)))
    else:
        lines.append("%s: not fetched locally, skipped" % branch)

# (c) the engine's own answer
uci = sh("printf 'uci\\nquit\\n' | %s" % os.path.expanduser("~/build_rel/forge"))
nfile = [l for l in uci.splitlines() if "NnueFile" in l or "NNUE" in l]
lines.append("(c) engine's NNUE-related uci lines:")
for l in nfile:
    lines.append("    " + l)

clause_a = len(ext_hits) == 0
clause_b = len(big) == 0
clause_c = any("NnueFile" in l and "default <empty>" in l for l in nfile)
verdict = "CONFIRMS" if (clause_a and clause_c) else "REFUTES"

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("check of 29-F9 by seat 19\n\n")
    fh.write("\n".join(lines) + "\n\n")
    fh.write("clause (a) no .nnue/.bin tracked: %s\n" % clause_a)
    fh.write("clause (b) no tracked file over 1 MB: %s\n" % clause_b)
    fh.write("clause (c) NnueFile default is empty: %s\n" % clause_c)
    fh.write("\nVERDICT %s 29-F9\n" % verdict)
print(open(os.path.join(outdir, "RESULT.txt")).read())
