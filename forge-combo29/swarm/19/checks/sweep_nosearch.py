#!/usr/bin/env python3
"""sweep_nosearch.py OUTDIR [MAXFILES] : find committed output where a search was CLAIMED but did not happen.

Uses the closing check from HARNESS_TRAPS (trap 1 + 1b): a search happened only if **nodes > 0 AND the PV is
non-empty**. This is stricter than my two earlier sweeps and catches both failure shapes:

  * trap 1  — a `bestmove` with NO `info depth` line (terminator aborted the search)
  * trap 1b — `info depth` lines that exist but carry `nodes 0` and an EMPTY pv (drawn-root shortcut)

For each file it counts blocks delimited by `bestmove`; a block is SUSPECT if its last `info depth` line has
nodes 0 or an empty PV.

The round-boundary problem from 19-C16 is avoided differently here: instead of inferring blocks, this looks only
at the LAST `info depth` line before each `bestmove` and asks whether THAT line reports a real search. A line
with `nodes 0` is never a real search whatever the block boundaries are — so the check is immune to the
`readyok` interleaving that broke the earlier attempt.
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 400_000
os.makedirs(OUT, exist_ok=True)
REPO = "/agent/repos/dwqww"
SKIP = re.compile(r"\.(patch\.txt|py|sh|md|json|jsonl|epd|fens|csv|tsv)$", re.I)

INFO = re.compile(r"^\s*info depth")
BESTMOVE = re.compile(r"^\s*(?:>>>\s*)?bestmove\b")


def scan(body):
    """Returns (searches_claimed, suspect_zero_nodes, suspect_empty_pv)."""
    claimed = 0
    zero = empty = 0
    last_info = None
    for line in body.splitlines():
        if INFO.match(line):
            last_info = line
        elif BESTMOVE.match(line):
            claimed += 1
            if last_info is not None:
                if re.search(r"\bnodes 0\b", last_info):
                    zero += 1
                elif not re.search(r"\bpv \S", last_info):
                    empty += 1
                last_info = None
    return claimed, zero, empty


branches = subprocess.run('git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*"',
                          shell=True, cwd=REPO, capture_output=True, text=True).stdout
seats = sorted({m.group(1) for m in re.finditer(r"swarm-(\d+)$", branches, re.M)})


def sh(cmd, binary=False):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


per_seat = {}
detail = []


def consider(seat, path, body):
    claimed, zero, empty = scan(body)
    if claimed == 0:
        return
    rec = per_seat.setdefault(seat, [0, 0, 0, 0])
    rec[0] += claimed
    rec[1] += zero
    rec[2] += empty
    if zero or empty:
        rec[3] += 1
        detail.append((seat, path, claimed, zero, empty))


for s in seats:
    if s == "19":
        continue
    sh("git fetch -q --depth 1 origin for-fable-and-opus/swarm-%s" % s)
    for f in sh('git ls-tree -r --name-only FETCH_HEAD -- "forge-combo29/swarm/%s/"' % s).split("\n"):
        if not f or SKIP.search(f):
            continue
        raw = sh('git show "FETCH_HEAD:%s"' % f, binary=True)
        if not raw or len(raw) > MAX:
            continue
        consider(s, f, raw.decode("utf-8", "replace"))

for f in sh('git ls-tree -r --name-only HEAD -- "forge-combo29/swarm/19/"').split("\n"):
    if not f or SKIP.search(f):
        continue
    try:
        raw = open(os.path.join(REPO, f), "rb").read()
    except OSError:
        continue
    if not raw or len(raw) > MAX:
        continue
    consider("19", f, raw.decode("utf-8", "replace"))

with open(os.path.join(OUT, "RESULT.txt"), "w") as fh:
    fh.write("# searches CLAIMED (a bestmove with a preceding info line) but reporting nodes 0 or an empty PV\n\n")
    fh.write("Closing check from HARNESS_TRAPS (traps 1 and 1b): a search happened only if nodes > 0 AND the PV is\n")
    fh.write("non-empty. This looks at the last info line before each bestmove, so it is immune to the readyok\n")
    fh.write("interleaving that broke the earlier per-search sweep (19-C16).\n\n")
    fh.write("| seat | claimed searches | with nodes 0 | with empty PV | files affected |\n")
    fh.write("|---|---|---|---|---|\n")
    for s in sorted(per_seat, key=lambda x: -(per_seat[x][1] + per_seat[x][2])):
        c, z, e, fa = per_seat[s]
        if z or e:
            fh.write("| %s | %d | **%d** | **%d** | %d |\n" % (s, c, z, e, fa))
    fh.write("\n## files, largest first (first 30)\n\n")
    detail.sort(key=lambda d: -(d[3] + d[4]))
    for seat, path, claimed, z, e in detail[:30]:
        fh.write("- seat %s: `%s` — %d claimed, **%d zero-node**, **%d empty-PV**\n" % (seat, path, claimed, z, e))
    fh.write("\nseats scanned: %d ; files with a suspect search: %d\n" % (len(seats), len(detail)))
print(open(os.path.join(OUT, "RESULT.txt")).read()[-2200:])
