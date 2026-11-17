#!/usr/bin/env python3
"""Sample N real positions from the repo's PGN chunks, validated with python-chess.

Writes JSON list of {fen, plies, source}.
"""
import glob
import json
import random
import sys

import chess
import chess.pgn

CHUNKS = sorted(glob.glob("/agent/repos/dwqww/forge-combo29/tests_r3fu_*/chunk*.pgn"))
CHUNKS += sorted(glob.glob("/agent/repos/dwqww/forge-combo29/tests_r3*/chunk*.pgn"))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261117
    rng = random.Random(seed)
    games = []
    for path in CHUNKS:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                while True:
                    g = chess.pgn.read_game(fh)
                    if g is None:
                        break
                    if g.errors:
                        continue
                    moves = list(g.mainline_moves())
                    if len(moves) < 30:
                        continue
                    games.append((path, moves, g.headers.get("FEN")))
        except Exception as exc:  # noqa: BLE001
            print(f"skip {path}: {exc}", file=sys.stderr)
    rng.shuffle(games)
    out = []
    seen = set()
    for path, moves, startfen in games:
        if len(out) >= n:
            break
        ply = rng.randrange(12, min(len(moves), 120))
        board = chess.Board(startfen) if startfen else chess.Board()
        ok = True
        for mv in moves[:ply]:
            if mv not in board.legal_moves:
                ok = False
                break
            board.push(mv)
        if not ok:
            continue
        if board.is_game_over(claim_draw=False):
            continue
        fen = board.fen(en_passant="fen")
        if fen in seen:
            continue
        # independent legality check of the fixture
        check = chess.Board(fen)
        if not check.is_valid():
            continue
        if check.status() != chess.STATUS_VALID:
            continue
        seen.add(fen)
        out.append({"fen": fen, "plies": ply, "source": path.split("/")[-2] + "/" + path.split("/")[-1]})
    json.dump(out, open(sys.argv[3] if len(sys.argv) > 3 else "/tmp/forge/positions.json", "w"), indent=1)
    print(f"games={len(games)} positions={len(out)}")


if __name__ == "__main__":
    main()
