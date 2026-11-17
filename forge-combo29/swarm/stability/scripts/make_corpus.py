"""Build a 200-position corpus of the kind a training corpus contains.

Provenance: engine self-play from RANDOM 8-ply openings. Both halves matter.
Random openings are the only legal source of variety (the audit records that
ten self-play games from one start produce ONE distinct game), and engine moves
after that are what a self-play corpus actually holds -- pure random-move games
drift into positions no corpus contains.

Each sampled position is emitted as a MOVE LIST from startpos, not a FEN,
because a FEN cannot carry repetition history and a corpus position is reached
by moves. The sampler records the ply and phase so the report can show the
corpus spans opening / middlegame / endgame rather than claiming it does.

Every FEN is validated with python-chess AND the engine's acceptance of the
position command is checked at measure time (a refused FEN silently re-searches
the previous board).
"""
import json
import os
import random
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ucih import Uci

FORGE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-stab/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "corpus.json"
GAMES = 44
# Sampled plies are spread deliberately across the game so the corpus holds
# opening, middlegame AND late positions rather than a 32-ply slice of one phase.
PICK = [14, 22, 30, 48, 70, 100]
OPENING_PLIES = 8
MAX_PLY = 104
SELFPLAY_DEPTH = 8
SEED0 = 20261117

OPTIONS = ["setoption name OwnBook value false",
           "setoption name Threads value 1",
           "setoption name Hash value 32",
           "setoption name MultiPV value 1"]


def pick_opening(rng):
    """Random legal 8-ply opening, distinct first move per game class."""
    b = chess.Board()
    for _ in range(OPENING_PLIES):
        moves = list(b.legal_moves)
        b.push(rng.choice(moves))
    return [m.uci() for m in b.move_stack]


def selfplay(u, moves, plies, depth):
    """Extend a move list with engine moves; return list of (ply, movelist)."""
    snapshots = []
    u.send("position startpos moves " + " ".join(moves))
    for ply in range(plies):
        r = u.search("position startpos moves " + " ".join(moves), f"go depth {depth}")
        if r["bestmove"] in (None, "0000"):
            break
        if r["bail"]:
            # adjudicated draw: the move was never searched. Stop this game here
            # rather than sample a position reached by an unsearched move.
            break
        moves = moves + [r["bestmove"]]
        snapshots.append((OPENING_PLIES + ply + 1, list(moves)))
        if len(moves) >= MAX_PLY:
            break
    return snapshots


def main():
    u = Uci(FORGE, timeout=300)
    corpus = []
    try:
        u.handshake()
        for o in OPTIONS:
            u.send(o)
        u.send("isready")
        while u.readline() != "readyok":
            pass

        gid = 0
        while len(corpus) < 200 and gid < GAMES:
            rng = random.Random(SEED0 + gid * 7919)
            opening = pick_opening(rng)
            snaps = selfplay(u, opening, MAX_PLY - OPENING_PLIES, SELFPLAY_DEPTH)
            by_ply = {ply: mv for ply, mv in snaps if ply in PICK}
            for ply in PICK:
                if ply not in by_ply:
                    continue
                mv = by_ply[ply]
                b = chess.Board()
                for m in mv:
                    b.push_uci(m)
                # python-chess validation, and one field it cannot close
                fen = b.fen()
                assert chess.Board(fen).is_valid(), (gid, ply)
                assert fen.split()[5] != "0", "fullmove 0 is engine-refused"
                corpus.append({
                    "id": f"g{gid:02d}p{ply:02d}",
                    "game": gid,
                    "ply": ply,
                    "moves": mv,
                    "fen": fen,
                    "phase": ("opening" if ply <= 16 else
                              "endgame" if len(b.piece_map()) <= 12 else "middlegame"),
                    "pieces": len(b.piece_map()),
                })
            gid += 1
    finally:
        u.close()

    corpus = corpus[:200]
    with open(OUT, "w") as f:
        json.dump(corpus, f, indent=1)
    from collections import Counter
    print(f"wrote {OUT}: {len(corpus)} positions from {gid} games")
    print("phase:", dict(Counter(c["phase"] for c in corpus)))
    print("plies:", dict(sorted(Counter(c["ply"] for c in corpus).items())))
    print("pieces min/median/max:",
          min(c["pieces"] for c in corpus),
          sorted(c["pieces"] for c in corpus)[len(corpus) // 2],
          max(c["pieces"] for c in corpus))


if __name__ == "__main__":
    main()
