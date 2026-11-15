#!/usr/bin/env python3
"""Compute score/Elo from a per-game file: round|white|black|result|fen.

Usage: elo_stats.py <games_file> <cand_name>

- s = (wins + draws/2) / games from cand's perspective.
- Elo = -400 * log10(1/s - 1).
- Interval: games are grouped into consecutive PAIRS (same opening, colours
  swapped). Pair score = (cand points in the 2 games) / 2 -> in {0, .25, .5,
  .75, 1}. m = mean, e = sample standard error (sd / sqrt(n)).
  Report Elo(m - 1.96 e) and Elo(m + 1.96 e).
- Elo is undefined at s in {0, 1}: prints "inf"/"-inf" instead of crashing.
"""
import math
import sys

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def elo(score: float) -> str:
    if score >= 1.0:
        return "inf"
    if score <= 0.0:
        return "-inf"
    return f"{-400.0 * math.log10(1.0 / score - 1.0):+.2f}"


def main() -> None:
    games_file, cand = sys.argv[1], sys.argv[2]
    games = []
    with open(games_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rnd, white, black, result, fen = line.split("|")
            games.append((int(rnd), white, black, result, fen))

    wins = losses = draws = 0
    pair_scores = []
    i = 0
    unpaired = 0
    while i < len(games):
        if i + 1 < len(games):
            a, b = games[i], games[i + 1]
            # A pair: same opening, colours swapped.
            if a[4] == b[4] and a[1] == b[2] and a[2] == b[1]:
                pa = pair_points(a, cand)
                pb = pair_points(b, cand)
                pair_scores.append((pa + pb) / 2.0)
                i += 2
                continue
        unpaired += 1
        i += 1

    for g in games:
        pts = pair_points(g, cand)
        if pts == 1.0:
            wins += 1
        elif pts == 0.0:
            losses += 1
        else:
            draws += 1

    n = len(games)
    s = (wins + draws / 2.0) / n
    m = sum(pair_scores) / len(pair_scores)
    if len(pair_scores) > 1:
        var = sum((x - m) ** 2 for x in pair_scores) / (len(pair_scores) - 1)
        e = math.sqrt(var / len(pair_scores))
    else:
        e = float("nan")
    lo = elo(min(max(m - 1.96 * e, 0.0), 1.0)) if e == e else "nan"
    hi = elo(min(max(m + 1.96 * e, 0.0), 1.0)) if e == e else "nan"

    counts: dict[float, int] = {}
    for x in pair_scores:
        counts[x] = counts.get(x, 0) + 1

    print(f"games {n} pairs {len(pair_scores)} unpaired {unpaired}")
    print(f"cand W-L-D {wins}-{losses}-{draws} score {s:.4f} "
          f"Elo {elo(s)}")
    print(f"pair mean {m:.4f} se {e:.4f} Elo95 [{lo}, {hi}]")
    print("pair score counts:",
          " ".join(f"{k}:{counts[k]}" for k in sorted(counts)))


def pair_points(g, cand: str) -> float:
    _, white, black, result, _ = g
    if result == "1-0":
        pts_white, pts_black = 1.0, 0.0
    elif result == "0-1":
        pts_white, pts_black = 0.0, 1.0
    else:
        pts_white = pts_black = 0.5
    return pts_white if white == cand else pts_black


if __name__ == "__main__":
    main()
