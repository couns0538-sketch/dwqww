#!/usr/bin/env python3
"""games_tsv.py (Opus, 20 November 2026), for the Grok swarm 2. Needs python-chess (PyPI).
  python3 games_tsv.py tsv  <games.pgn> <out.tsv>   one line per game: white black result plies termination fen sha
  python3 games_tsv.py pool <side> <a.tsv> [<b.tsv> ...]   pairs (the two games of one opening FEN), for <side>:
      W-L-D, pentanomial [0, 0.5, 1, 1.5, 2 points a pair], Elo and its 95 % interval from the pair scores"""
import hashlib
import math
import sys

import chess.pgn


def tsv(pgn_path, out_path):
    n = 0
    with open(pgn_path, encoding="utf-8", errors="replace") as f, open(out_path, "w", encoding="utf-8") as o:
        while True:
            g = chess.pgn.read_game(f)
            if g is None:
                break
            h = g.headers
            moves = [m.uci() for m in g.mainline_moves()]
            if g.errors:
                sys.exit(f"STOP: game {n + 1} of {pgn_path} does not parse: {g.errors[0]}")
            sha = hashlib.sha1(" ".join(moves).encode()).hexdigest()[:12]
            row = [h.get("White", "?"), h.get("Black", "?"), h.get("Result", "*"), str(len(moves)),
                   h.get("Termination", "?").replace(" ", "_"), h.get("FEN", "startpos"), sha]
            o.write("\t".join(row) + "\n")
            n += 1
    print(f"{n} games -> {out_path}")


def pool(side, paths):
    by_fen = {}
    for p in paths:
        for line in open(p, encoding="utf-8"):
            white, black, result, plies, term, fen, sha = line.rstrip("\n").split("\t")
            pts = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}.get(result)
            if pts is None or side not in (white, black):
                sys.exit(f"STOP: unscored game or side {side} not playing in {p}: {line.strip()}")
            by_fen.setdefault(fen, []).append(pts if white == side else 1.0 - pts)
    bad = sum(1 for v in by_fen.values() if len(v) != 2)
    pairs = [sum(v) for v in by_fen.values() if len(v) == 2]
    games = [x for v in by_fen.values() for x in v]
    w, l = games.count(1.0), games.count(0.0)
    d = len(games) - w - l
    ptn = [sum(1 for s in pairs if abs(s - k / 2) < 1e-9) for k in range(5)]
    n = len(pairs)
    mean = sum(pairs) / (2 * n)
    var = sum((s / 2 - mean) ** 2 for s in pairs) / n
    half = 1.96 * math.sqrt(var / n)
    elo = lambda s: -400 * math.log10(1 / min(max(s, 1e-6), 1 - 1e-6) - 1)
    print(f"side {side}: games {len(games)} W-L-D {w}-{l}-{d} pairs {n} (openings not in exactly 2 games: {bad})")
    print(f"ptnml {ptn} Elo {elo(mean):+.2f} 95% [{elo(mean - half):+.2f}, {elo(mean + half):+.2f}]")


if __name__ == "__main__":
    if sys.argv[1] == "tsv":
        tsv(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "pool":
        pool(sys.argv[2], sys.argv[3:])
    else:
        sys.exit(__doc__)
