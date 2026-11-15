#!/usr/bin/env python3
# Pair-shape check: is a fastchess min PGN's per-round cand score distribution
# the degenerate [0,0,N,0,0] (identical play both sides) or not?
import re
import sys

def main(path, cand_name):
    tags = {}
    rounds = {}
    cur = None
    for line in open(path, encoding="utf-8", errors="replace"):
        if line.startswith('[Event "'):
            cur = {}
        m = re.match(r'\[(\w+) "(.*?)"\]\s*$', line)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2)
        if line.startswith("\n") and cur:
            r = cur.get("Round", "?")
            res = cur.get("Result", "?")
            white = cur.get("White", "?")
            pts = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == (white == cand_name) else 0.0)
            rounds.setdefault(r, []).append(pts)
            cur = None
    counts = [0, 0, 0, 0, 0]
    for g in rounds.values():
        counts[min(4, max(0, int(round(sum(g) * 2))))] += 1
    deg = counts[0] == 0 and counts[1] == 0 and counts[3] == 0 and counts[4] == 0
    print("DEGENERATE" if deg else f"OK {counts}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
