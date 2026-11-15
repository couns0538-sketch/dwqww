#!/usr/bin/env python3
"""Job 4 numbers: per-match Elo from the pairs, and pooled over the two seeds of
each idea.  A pair is one round (same opening, colours reversed); its score is
0, 0.5, 1, 1.5 or 2 points out of 2, which is the pentanomial.  The 95% interval
is the same transform applied to score +/- 1.96*se.

Reads the derived per-game files (`logs/<match>.games.txt`), which are made from
each match's PGN; PGNs themselves are not committed.
"""
import math
import re
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent / "logs"
Z = 1.959963985


def elo(m):
    if m <= 0:
        return float("-inf")
    if m >= 2:
        return float("inf")
    return 400.0 * math.log10(m / (2.0 - m))


def read_pairs(path):
    if not path.exists():
        return None
    rounds = {}
    wins = losses = draws = 0
    for line in path.read_text().splitlines():
        r = re.search(r"round=(\d+)", line)
        w = re.search(r"white=(\w+)", line)
        res = re.search(r"result=(\S+)", line)
        if not (r and w and res):
            continue
        rnd, white, result = int(r.group(1)), w.group(1), res.group(1)
        if result == "1/2-1/2":
            pts = 0.5
            draws += 1
        elif result == "1-0":
            pts = 1.0 if white == "cand" else 0.0
        elif result == "0-1":
            pts = 0.0 if white == "cand" else 1.0
        else:
            continue
        if result != "1/2-1/2":
            if (result == "1-0") == (white == "cand"):
                wins += 1
            else:
                losses += 1
        rounds.setdefault(rnd, []).append(pts)
    counts = [0, 0, 0, 0, 0]
    for rnd, pts in rounds.items():
        if len(pts) == 2:
            counts[int(round(sum(pts) / 0.5))] += 1
    return counts, (wins, losses, draws)


def stats(counts):
    n = sum(counts)
    scores = [0.0, 0.5, 1.0, 1.5, 2.0]
    mean = sum(c * s for c, s in zip(counts, scores)) / n
    var = sum(c * (s - mean) ** 2 for c, s in zip(counts, scores)) / max(1, n - 1)
    se = math.sqrt(var / n)
    lo, hi = max(0.0, mean - Z * se), min(2.0, mean + Z * se)
    return mean, elo(mean), elo(lo), elo(hi), n


def main():
    matches = [("control", "control", "20000 vs 10000 nodes"),
               ("M1", "M1", "CorrMargin 20 (mild)"),
               ("M2", "M2", "CorrMargin 20 (mild)"),
               ("M3", "M3", "CorrMargin 64 (strong)"),
               ("M4", "M4", "CorrMargin 64 (strong)")]
    print(f"{'match':<8} {'setting':<28} {'games':>6} {'pairs':>6} {'W-L-D':>14} {'pair counts':>24} "
          f"{'Elo':>8} {'95% interval':>20}")
    for key, fname, label in matches:
        got = read_pairs(LOGS / f"{fname}.games.txt")
        if got is None:
            print(f"{key:<8} {str(label):<28} (no games file)")
            continue
        counts, (w, l, d) = got
        if sum(counts) == 0:
            print(f"{key:<8} {str(label):<28} no complete pairs")
            continue
        m, e, lo, hi, n = stats(counts)
        print(f"{key:<8} {str(label):<28} {w+l+d:>6} {n:>6} {f'{w}-{l}-{d}':>14} {str(counts):>24} "
              f"{e:>+8.2f} {lo:+8.1f} .. {hi:+.1f}")

    for label, names in (("CorrMargin 20 pooled (M1+M2)", ["M1", "M2"]), ("CorrMargin 64 pooled (M3+M4)", ["M3", "M4"])):
        total = [0, 0, 0, 0, 0]
        w = l = d = 0
        for nm in names:
            got = read_pairs(LOGS / f"{nm}.games.txt")
            if got:
                total = [a + b for a, b in zip(total, got[0])]
                w, l, d = w + got[1][0], l + got[1][1], d + got[1][2]
        if sum(total):
            m, e, lo, hi, n = stats(total)
            print()
            print(f"{label}: games {w+l+d} ({w}-{l}-{d}) pairs {n} counts {total}")
            print(f"  pooled Elo {e:+.2f}, 95% interval {lo:+.1f} .. {hi:+.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
