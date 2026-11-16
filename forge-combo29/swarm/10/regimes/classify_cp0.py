#!/usr/bin/env python3
"""classify_cp0.py FILE -- classify every `score cp 0` record in recorded engine output.

Two mechanisms print `cp 0` and they must not be confused:
   ROOT_SHORTCUT : pv EMPTY and 0 nodes  -> no search happened (halfmove >= 100 on the base tree)
   HORIZON       : pv NON-EMPTY          -> the fifty-move horizon fired inside the tree, at ANY node count

A node threshold does NOT work: measured horizon records carried 200..13,791,896 nodes across four bare
endgames, and a 10,000-node cut misclassified 6 of 6. The pv is the discriminator.

Exit code 0 always (this classifies, it does not judge); the summary prints counts per class.
"""
import re
import sys


def records(text):
    out, cur = [], []
    for line in text.splitlines():
        cur.append(line)
        if line.startswith("bestmove"):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def classify(lines):
    infos = [l for l in lines if l.startswith("info depth")]
    if not infos:
        return None
    last = infos[-1]
    m = re.search(r" score (cp|mate) (-?\d+)", last)
    if not m or m.group(1) != "cp" or int(m.group(2)) != 0:
        return None                      # not a zero-scored record
    nodes = None
    n = re.search(r" nodes (\d+)", last)
    if n:
        nodes = int(n.group(1))
    pv = last.split(" pv ", 1)[1].split() if " pv " in last else []
    if not pv and nodes == 0:
        return ("ROOT_SHORTCUT", nodes, 0)
    if pv:
        return ("HORIZON", nodes, len(pv))
    if not pv and nodes is not None and nodes > 0:
        return ("AMBIGUOUS_no_pv_but_searched", nodes, 0)
    return ("UNKNOWN", nodes, len(pv))


def main():
    text = open(sys.argv[1], errors="replace").read()
    counts = {}
    for i, r in enumerate(records(text)):
        c = classify(r)
        if c is None:
            continue
        counts[c[0]] = counts.get(c[0], 0) + 1
        print("record %d: %-10s nodes %-9s pv %d" % (i, c[0], c[1], c[2]))
    print()
    print("cp 0 records:", sum(counts.values()), dict(counts))
    print("rule: empty pv + 0 nodes = ROOT_SHORTCUT; non-empty pv = HORIZON (any node count)")


if __name__ == "__main__":
    main()
