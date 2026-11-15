#!/usr/bin/env python3
"""Pooled Elo for job 3: the two seeds of each divisor combined.

The result the job asks for is the POOLED number of the two matches at a
divisor, not either match alone.  Pooling is done on the pairs: the pair counts
of the two matches are added, and the same pentanomial interval is computed on
the sum.  This is legitimate because the two matches use disjoint seeds
(different openings), so their pairs are independent samples of the same
comparison.

Also reports each match alone, and the per-divisor split, so the pooled figure
can be checked against its parts.
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


def pair_counts(games_path):
    """Pentanomial from a derived per-game file: a pair is one Round.

    The per-game files are made from the match PGNs (round, colours, opening,
    result); PGNs themselves are not committed because of their size.
    """
    if not games_path.exists():
        return None
    rounds = {}
    for line in games_path.read_text().splitlines():
        rnd = re.search(r"round=(\d+)", line)
        white = re.search(r"white=(\w+)", line)
        result = re.search(r"result=(\S+)", line)
        if not (rnd and white and result):
            continue
        r, w, res = int(rnd.group(1)), white.group(1), result.group(1)
        if res == "1/2-1/2":
            pts = 0.5
        elif res == "1-0":
            pts = 1.0 if w == "cand" else 0.0
        elif res == "0-1":
            pts = 0.0 if w == "cand" else 1.0
        else:
            continue
        rounds.setdefault(r, []).append(pts)
    counts = [0, 0, 0, 0, 0]
    for r, pts in rounds.items():
        if len(pts) == 2:
            counts[int(round(sum(pts) / 0.5))] += 1
    return counts


def stats(counts):
    n = sum(counts)
    scores = [0.0, 0.5, 1.0, 1.5, 2.0]
    mean = sum(c * s for c, s in zip(counts, scores)) / n
    var = sum(c * (s - mean) ** 2 for c, s in zip(counts, scores)) / (n - 1)
    se = math.sqrt(var / n)
    lo, hi = max(0.0, mean - Z * se), min(2.0, mean + Z * se)
    return mean, elo(mean), elo(lo), elo(hi), n


def main():
    groups = {
        "D=8192 (first divisor)": ["p5-M1", "p5-M2"],
        "D=2048 (second divisor)": ["p5-M3", "p5-M4"],
    }
    print(f"{'match':<26} {'pairs':>6} {'pair counts':>26} {'score':>7} {'Elo':>8} {'95% interval':>20}")
    for label, names in groups.items():
        total = [0, 0, 0, 0, 0]
        for nm in names:
            c = pair_counts(LOGS / f"{nm}.games.txt")
            if c is None:
                print(f"{nm:<26} no pgn")
                continue
            m, e, lo, hi, n = stats(c)
            print(f"{nm:<26} {n:>6} {str(c):>26} {m:>7.3f} {e:>+8.2f} {lo:+8.1f} .. {hi:+.1f}")
            total = [a + b for a, b in zip(total, c)]
        m, e, lo, hi, n = stats(total)
        print(f"{label:<26} {n:>6} {str(total):>26} {m:>7.3f} {e:>+8.2f} {lo:+8.1f} .. {hi:+.1f}"
              f"   <== POOLED")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
