#!/usr/bin/env python3
"""recount24.py -- my own recount of glmflash5's match gamelists (jobs 25, 26, 27).
Per match: game W-L-D, the five pair outcomes (pair score 2/1.5/1/0.5/0), pair Elo with its
95 percent interval, and the distinct-opening set. Cross-match opening sharing."""
import itertools
import math
import sys
from collections import Counter

def parse(path):
    games = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        idx, white, black, result, term, fen = line.split("|", 5)
        cand_is_white = white == "cand"
        if result == "1-0":
            sc = 1.0 if cand_is_white else 0.0
        elif result == "0-1":
            sc = 0.0 if cand_is_white else 1.0
        else:
            sc = 0.5
        games.append((fen, sc))
    return games

def recount(path):
    games = parse(path)
    by_opening = {}
    for fen, sc in games:
        by_opening.setdefault(fen, []).append(sc)
    pairs = []
    for fen, scs in by_opening.items():
        if len(scs) != 2:
            return dict(error=f"opening appears {len(scs)} times: {fen[:40]}")
        pairs.append((fen, sum(scs) / 2.0))  # pair score in {0, .5, 1}
    n = len(pairs)
    w = sum(1 for _, s in games if s == 1.0)
    l = sum(1 for _, s in games if s == 0.0)
    d = sum(1 for _, s in games if s == 0.5)
    outcome = Counter(round(p * 4) for _, p in pairs)  # p in {0,.25,.5,.75,1} exact
    five = {2.0: outcome.get(4, 0), 1.5: outcome.get(3, 0), 1.0: outcome.get(2, 0),
            0.5: outcome.get(1, 0), 0.0: outcome.get(0, 0)}
    m = sum(p for _, p in pairs) / n
    var = sum((p - m) ** 2 for _, p in pairs) / n
    if m <= 0 or m >= 1:
        elo, lo, hi = (float("-inf") if m <= 0 else float("inf")), None, None
    else:
        elo = -400 * math.log10(1 / m - 1)
        sd = 400 / (math.log(10) * m * (1 - m)) * math.sqrt(var / n)
        lo, hi = elo - 1.959964 * sd, elo + 1.959964 * sd
    return dict(games=len(games), w=w, l=l, d=d, pairs=n, five=five, elo=elo, lo=lo, hi=hi,
                openings={fen for fen, _ in pairs}, mean=m)

JOBS = {25: ["M61", "M62", "M63", "M64", "M65", "M66"],
        26: ["M67", "M68", "M69", "M70", "M71", "M72"],
        27: ["M73", "M74", "M75", "M76", "M77"],
        24: ["M60"]}

allsets = {}
for job, ms in JOBS.items():
    for mm in ms:
        r = recount(f"/tmp/gm/{job}_gamelist_{mm}.txt")
        if "error" in r:
            print(f"{mm}: ERROR {r['error']}")
            continue
        allsets[mm] = r["openings"]
        f5 = " ".join(f"{k}:{v}" for k, v in sorted(r["five"].items(), reverse=True))
        print(f"{mm}: games {r['games']} W-L-D {r['w']}-{r['l']}-{r['d']} pairs {r['pairs']} "
              f"outcomes[{f5}] elo {r['elo']:+.2f} [{r['lo']:+.2f}, {r['hi']:+.2f}]")
print("== distinct-openings shared between any two matches (nonzero only):")
nz = 0
for a, b in itertools.combinations(sorted(allsets), 2):
    s = len(allsets[a] & allsets[b])
    if s:
        nz += 1
        print(f"{a} & {b}: {s}")
print(f"pairs of matches with nonzero sharing: {nz} of {len(list(itertools.combinations(allsets, 2)))}")
