#!/usr/bin/env python3
"""Extreme-material corpus, ALL positions legal and LIVE (not checkmate /
stalemate), so a search over them cannot return 0 nodes for a terminal reason.

A zero-node probe is indistinguishable from a vacuous probe unless the position
is known to be live. The first version of this corpus had 4 of 11 positions in
checkmate, which produced 4 zero-node searches that looked like coverage.

Every position here has a legal move for the side to move, so a 0-node search
would be a genuine defect and not a terminal position.
"""
import json
import random

import chess

rng = random.Random(20261117)


def live(board):
    if board.status() != chess.STATUS_VALID:
        return False
    tmp = board.copy()
    tmp.turn = not board.turn
    if tmp.is_check():          # the side NOT to move may not be in check
        return False
    return board.legal_moves.count() > 0


def build(fn, tries=400000):
    for _ in range(tries):
        b = fn()
        if b is not None and live(b):
            return b
    return None


def queens(nw, nb):
    def make():
        sq = list(range(64))
        rng.shuffle(sq)
        b = chess.Board(None)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        i = 2
        for s in sq[i:i + nw]:
            b.set_piece_at(s, chess.Piece(chess.QUEEN, chess.WHITE))
        i += nw
        for s in sq[i:i + nb]:
            b.set_piece_at(s, chess.Piece(chess.QUEEN, chess.BLACK))
        b.turn = chess.WHITE
        return b
    return make


def knights(n):
    def make():
        sq = list(range(64))
        rng.shuffle(sq)
        b = chess.Board(None)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        for s in sq[2:2 + n]:
            b.set_piece_at(s, chess.Piece(chess.KNIGHT, chess.WHITE))
        for s in sq[2 + n:2 + 2 * n]:
            b.set_piece_at(s, chess.Piece(chess.KNIGHT, chess.BLACK))
        b.turn = chess.WHITE
        return b
    return make


def mixed(nq):
    def make():
        sq = list(range(64))
        rng.shuffle(sq)
        b = chess.Board(None)
        b.set_piece_at(sq[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sq[1], chess.Piece(chess.KING, chess.BLACK))
        i = 2
        for color in (chess.WHITE, chess.BLACK):
            for _ in range(nq):
                b.set_piece_at(sq[i], chess.Piece(chess.QUEEN, color))
                i += 1
            for pt in (chess.ROOK, chess.BISHOP, chess.KNIGHT):
                b.set_piece_at(sq[i], chess.Piece(pt, color))
                i += 1
        b.turn = chess.WHITE
        return b
    return make


def main():
    out = []
    specs = [
        ("9v9 queens", queens(9, 9)),
        ("9v0 queens", queens(9, 0)),
        ("0v9 queens", queens(0, 9)),
        ("8v8 queens", queens(8, 8)),
        ("7v7 queens", queens(7, 7)),
        ("5v5 queens", queens(5, 5)),
        ("9v8 queens", queens(9, 8)),
        ("12 knights each", knights(12)),
        ("9 queens + pieces", mixed(9)),
        ("8 queens + pieces", mixed(8)),
    ]
    for label, fn in specs:
        for attempt in range(8):
            b = build(fn)
            if b is None:
                print(f"FAILED to build live: {label}")
                break
            fen = b.fen()
            if any(r["fen"] == fen for r in out):
                continue
            out.append({"fen": fen, "label": label, "attempt": attempt,
                        "legal_moves": b.legal_moves.count(),
                        "valid": True, "live": True})
            break
    b = chess.Board()
    out.append({"fen": b.fen(), "label": "startpos control",
                "legal_moves": 20, "valid": True, "live": True})

    for r in out:
        chk = chess.Board(r["fen"])
        assert chk.status() == chess.STATUS_VALID, r
        assert chk.legal_moves.count() > 0, r
        print(f'{r["legal_moves"]:4d} moves  {r["label"]:22s} {r["fen"]}')
    json.dump(out, open("/tmp/forge/stress_positions.json", "w"), indent=1)
    print(f"\nkept {len(out)} live positions")


if __name__ == "__main__":
    main()
