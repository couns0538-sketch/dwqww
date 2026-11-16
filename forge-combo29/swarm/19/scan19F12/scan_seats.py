#!/usr/bin/env python3
"""scan_seats.py OUTDIR : scan EVERY seat's committed files for the signature of 19-F12.

19-F12: a terminator sent while a search runs makes this build answer `bestmove a2a3` with 0 nodes. If a
seat's harness blind-piped its command stream, its committed raw output should contain searches that
reported no nodes at all, or repeated identical `bestmove a2a3`.

For each seat branch, this fetches the file list and greps every text file under forge-combo29/swarm/<seat>/
for two signals:
  S1  a line `bestmove a2a3` occurring more than half the number of `bestmove` lines (a blind-pipe would give
      100 %, since a2a3 is simply the first legal move of startpos)
  S2  the literal ` nodes 0` (a zero-node search)
and prints the file, the counts, and a verdict per file. It only inspects; nothing is written to any seat.

This is a check OF the swarm's own data, not a claim about any seat's honesty: a seat whose harness waits for
`bestmove` (like seat 24's driver) is immune and should show clean.
"""
import os
import re
import subprocess
import sys

outdir = sys.argv[1]
os.makedirs(outdir, exist_ok=True)
REPO = "/agent/repos/dwqww"


def sh(cmd, binary=False):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True)
    if binary:
        return r.stdout
    return r.stdout.decode("utf-8", errors="replace")


branches = sh('git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*"')
seats = sorted({m.group(1) for m in re.finditer(r"swarm-(\d+)$", branches, re.M)})

rows = []
for seat in seats:
    if seat == "19":
        continue
    sh("git fetch -q --depth 1 origin for-fable-and-opus/swarm-%s" % seat)
    files = sh('git ls-tree -r --name-only FETCH_HEAD -- "forge-combo29/swarm/%s/"' % seat).split("\n")
    for path in files:
        if not path or path.endswith(".patch.txt"):
            continue
        body = sh('git show "FETCH_HEAD:%s"' % path)
        if not body:
            continue
        best = len(re.findall(r"^bestmove", body, re.M))
        a2a3 = len(re.findall(r"^bestmove a2a3", body, re.M))
        zero = len(re.findall(r" nodes 0\b", body))
        if best >= 4 and a2a3 == best:
            rows.append((seat, path, best, a2a3, zero, "ALL bestmoves are a2a3"))
        elif zero >= 4:
            rows.append((seat, path, best, a2a3, zero, "many zero-node searches"))

with open(os.path.join(outdir, "RESULT.txt"), "w") as fh:
    fh.write("scan of %d seat branches for the 19-F12 signature\n" % len(seats))
    fh.write("signal S1: every bestmove in a file is a2a3 (what a blind-piped harness produces)\n")
    fh.write("signal S2: four or more ` nodes 0` occurrences (zero-node searches)\n\n")
    if not rows:
        fh.write("no file showed either signal.\n")
        fh.write("NOTE: this is a scan of COMMITTED TEXT, not proof that a seat's harness was correct —\n")
        fh.write("a harness can be immune and still not commit per-search node counts.\n")
    else:
        fh.write("| seat | file | bestmove lines | of them a2a3 | ` nodes 0` | signal |\n")
        fh.write("|---|---|---|---|---|---|\n")
        for r in rows:
            fh.write("| %s | `%s` | %d | %d | %d | %s |\n" % r)
print(open(os.path.join(outdir, "RESULT.txt")).read())
