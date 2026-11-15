#!/usr/bin/env python3
"""Own Elo + 95% interval from the pentanomial pair counts, and from the game list.

Two numbers are produced for every match, as job 2 asks:

  * fastchess's Elo +/- error, copied from its own final (or last) summary block;
  * my Elo from the pairs, with a 95% interval.

The pair method.  A "pair" is the two games of one round, same opening, colours
swapped.  Its score is 0, 0.5, 1, 1.5 or 2 points out of 2, which is exactly the
pentanomial fastchess prints as Ptnml(0-2).  The pair scores are independent, so
    mean  m = sum(pair_score)/pairs
    var   = sum((pair_score - m)^2) / (pairs - 1)        (sample variance)
    se_m  = sqrt(var / pairs)
Elo = 400*log10(m/(2-m)) if 0 < m < 2 else +/-inf, and the interval is that
transform applied to m +/- 1.96*se_m.  This is the standard pentanomial interval
and it is computed here rather than read off fastchess, so the two can disagree.

For a match cut short, fastchess's last printed block lags the games actually
played (it prints every -ratinginterval).  Where a games.txt exists the pair
counts are recomputed from the games themselves, and both the recomputed count
and fastchess's last printed count are shown.
"""
import math
import re
import sys
from pathlib import Path

LOGS = Path(__file__).resolve().parent / "logs"
Z = 1.959963985


def elo_from_score(m):
    if m <= 0.0:
        return float("-inf")
    if m >= 2.0:
        return float("inf")
    return 400.0 * math.log10(m / (2.0 - m))


def fastchess_block(directory):
    """Last summary block fastchess printed."""
    path = LOGS / directory / "full.txt"
    if not path.exists():
        return None
    text = path.read_text().splitlines()
    elo = games = ptn = None
    for i, line in enumerate(text):
        if line.startswith("Elo:"):
            m = re.match(r"Elo:\s*(-?[\d.]+)\s*\+/-\s*([\d.]+)", line)
            if m:
                elo = (float(m.group(1)), float(m.group(2)))
                games = ptn = None
                for follow in text[i:i + 8]:
                    g = re.match(r"Games:\s*(\d+)", follow)
                    if g:
                        games = int(g.group(1))
                    p = re.match(r"Ptnml\(0-2\):\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]", follow)
                    if p:
                        ptn = [int(p.group(k)) for k in range(1, 6)]
    return elo, games, ptn


def pairs_from_games(directory):
    """Recompute pair scores and W-L-D from games.txt.  A pair = one round."""
    path = LOGS / directory / "games.txt"
    if not path.exists():
        return None
    rounds = {}
    wins = losses = draws = 0
    for line in path.read_text().splitlines():
        m = re.match(r"round=(\d+) white=(\w+) black=(\w+)", line)
        r = re.search(r"result=(\S+)", line)
        if not m or not r:
            continue
        rnd, white, result = int(m.group(1)), m.group(2), r.group(1)
        if result == "1/2-1/2":
            cand_pts = 0.5
            draws += 1
        elif result == "1-0":
            cand_pts = 1.0 if white == "cand" else 0.0
        elif result == "0-1":
            cand_pts = 0.0 if white == "cand" else 1.0
        else:
            continue
        if result != "1/2-1/2":
            if (result == "1-0") == (white == "cand"):
                wins += 1
            else:
                losses += 1
        rounds.setdefault(rnd, []).append(cand_pts)
    counts = [0, 0, 0, 0, 0]
    for rnd, pts in rounds.items():
        if len(pts) != 2:
            continue          # a half-played pair is not scored
        counts[int(round(sum(pts) / 0.5))] += 1
    counts.append((wins, losses, draws))     # carried through for the table
    return counts


def pentanomial_elo(counts):
    counts = counts[:5]
    n = sum(counts)
    if n == 0:
        return None
    scores = [0.0, 0.5, 1.0, 1.5, 2.0]
    mean = sum(c * s for c, s in zip(counts, scores)) / n
    if n < 2:
        return mean, None, None
    var = sum(c * (s - mean) ** 2 for c, s in zip(counts, scores)) / (n - 1)
    se = math.sqrt(var / n)
    lo = max(0.0, mean - Z * se)
    hi = min(2.0, mean + Z * se)
    return mean, elo_from_score(mean), (elo_from_score(lo), elo_from_score(hi)), se


def main():
    directories = sorted(p.name for p in LOGS.iterdir() if p.is_dir() and p.name.startswith("M"))
    print("own Elo = pentanomial from the pairs (95% interval); W-L-D from the games")
    print(f"{'match':<22} {'cand W-L-D':>14} {'games':>6} {'pairs':>6} {'pair counts':>26} "
          f"{'own Elo':>8} {'95% interval':>20} {'fastchess':>18}")
    for d in directories:
        block = fastchess_block(d)
        rec = pairs_from_games(d)
        fc = f"{block[0][0]:+.2f}+/-{block[0][1]:.2f}" if block and block[0] else "--"
        if not rec:
            print(f"{d:<22} no games.txt")
            continue
        counts, wld = rec[:5], rec[5]
        res = pentanomial_elo(counts)
        if not res:
            print(f"{d:<22} no pairs")
            continue
        mean, elo, interval, se = res
        own = f"{elo:+.2f}" if elo is not None and math.isfinite(elo) else "--"
        iv = (f"{interval[0]:+.1f} .. {interval[1]:+.1f}"
              if interval and all(math.isfinite(x) for x in interval) else "--")
        print(f"{d:<22} {wld[0]:>4}-{wld[1]}-{wld[2]:<5} {wld[0]+wld[1]+wld[2]:>6} "
              f"{sum(counts):>6} {str(counts):>26} {own:>8} {iv:>20} {fc:>18}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
