#!/usr/bin/env python3
"""Job 9: recompute Elo and its error from a fastchess PGN, using Fable's recipe.

score s = (wins + draws/2) / games;  Elo = -400*log10(1/s - 1)
PAIR scores: the two games of one opening (colours reversed) give one pair score in
{0, 0.5, 1, 1.5, 2} points, divided by 2 -> {0, .25, .5, .75, 1}. Mean m and standard
error e over pairs; convert m-1.96e and m+1.96e the same way.

Usage: elo_from_pgn.py <pgn> [cand-name]
"""
import math
import re
import sys


def elo_of(score):
    if score <= 0.0:
        return -math.inf
    if score >= 1.0:
        return math.inf
    return -400.0 * math.log10(1.0 / score - 1.0)


def main():
    path = sys.argv[1]
    cand = sys.argv[2] if len(sys.argv) > 2 else None
    text = open(path, errors="replace").read()
    games = []
    # fastchess separates games with a single blank line; split on the [Event tag.
    blocks = re.split(r'(?=\[Event )', text)
    for block in blocks:
        if "[Event" not in block:
            continue
        white = re.search(r'\[White "([^"]+)"\]', block)
        black = re.search(r'\[Black "([^"]+)"\]', block)
        result = re.search(r'\[Result "([^"]+)"\]', block)
        if not (white and black and result):
            continue
        games.append((white.group(1), black.group(1), result.group(1)))
    if not games:
        raise SystemExit("no games parsed")
    # Candidate is whichever name is not the baseline; default the first name seen.
    names = {g[0] for g in games} | {g[1] for g in games}
    if cand is None:
        cand = sorted(names)[0]
    wins = losses = draws = 0
    for w, b, r in games:
        if r == "1/2-1/2":
            draws += 1
            continue
        if r not in ("1-0", "0-1"):
            continue
        winner = w if r == "1-0" else b
        if winner == cand:
            wins += 1
        else:
            losses += 1
    n = wins + losses + draws
    score = (wins + 0.5 * draws) / n
    elo = elo_of(score)

    # Pair them: fastchess -repeat plays opening i twice, colours reversed, consecutively.
    pairs = []
    i = 0
    while i + 1 < len(games):
        w1, b1, r1 = games[i]
        w2, b2, r2 = games[i + 1]
        pts = 0.0
        for w, b, r in ((w1, b1, r1), (w2, b2, r2)):
            if r == "1/2-1/2":
                pts += 0.5
            elif r == "1-0":
                pts += 1.0 if w == cand else 0.0
            elif r == "0-1":
                pts += 1.0 if b == cand else 0.0
        pairs.append(pts / 2.0)      # 0, .25, .5, .75, 1
        i += 2
    m = sum(pairs) / len(pairs)
    if len(pairs) > 1:
        var = sum((p - m) ** 2 for p in pairs) / (len(pairs) - 1)
        e = math.sqrt(var / len(pairs))
    else:
        e = 0.0
    lo, hi = elo_of(m - 1.96 * e), elo_of(m + 1.96 * e)
    print(f"file {path}")
    print(f"  games {n}: W {wins} L {losses} D {draws}  score {score:.4f}")
    print(f"  Elo (all games)      {elo:+.2f}")
    print(f"  pairs {len(pairs)}  mean {m:.4f}  se {e:.4f}")
    print(f"  Elo from pairs       {elo_of(m):+.2f}   95% interval [{lo:+.2f}, {hi:+.2f}]")


if __name__ == "__main__":
    main()
