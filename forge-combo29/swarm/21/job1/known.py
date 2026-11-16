#!/usr/bin/env python3
"""known.py EXE OUTDIR

Checks the two "known" statements of the brief's area 1 / job 1 against THIS build,
and quantifies the impossible-castling leniency with perft 3 versus python-chess.
Every case is one fresh process; raw output kept per case.
"""
import os
import subprocess
import sys

import chess

FENS = [
    # castling right claimed while a rook/king is missing or displaced
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",     # legal control
    "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1",          # rights, no rooks
    "4k3/8/8/8/8/8/8/R3K3 w Kk - 0 1",           # right K, rook a1
    "r3k2r/8/8/8/8/8/8/4K3 b kq - 0 1",          # black rights only, white no king-side
    "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1",
    # a triple check by knights (white king in check from three knights)
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
]

# Build a genuine triple-check position with python-chess by search over knight placements.
def find_triple_check():
    for knights in [(0, 1, 2), (8, 10, 12)]:
        pass
    # white king e4; knights that attack e4: c3,c5,d2,d6,f2,f6,g3,g5
    king = chess.E4
    attackers = [chess.C3, chess.D2, chess.G5]
    board = chess.Board(None)
    board.set_piece_at(king, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(chess.A1, chess.Piece(chess.KING, chess.BLACK))
    for sq in attackers:
        board.set_piece_at(sq, chess.Piece(chess.KNIGHT, chess.BLACK))
    board.turn = chess.WHITE
    return board.fen(), len(board.attackers(chess.WHITE, king)) if hasattr(board, "attackers") else None


def perft_py(fen, depth):
    try:
        b = chess.Board(fen)
    except Exception as exc:
        return None, type(exc).__name__
    if not b.is_valid() and b.status() != chess.STATUS_VALID:
        pass

    def rec(board, d):
        if d == 0:
            return 1
        total = 0
        for m in board.legal_moves:
            board.push(m)
            total += rec(board, d - 1)
            board.pop()
        return total

    return rec(b, depth), "ok"


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    triple_fen, natt = find_triple_check()
    FENS.append(triple_fen)
    rows = []
    for i, fen in enumerate(FENS):
        script = ["position fen " + fen, "isready", "go perft 3", "quit"]
        env = dict(os.environ)
        for k in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
            env.pop(k, None)
        proc = subprocess.run([exe], input="\n".join(script) + "\n", text=True,
                              capture_output=True, timeout=300, env=env)
        raw = os.path.join(outdir, "known_%02d.txt" % i)
        with open(raw, "w") as fh:
            fh.write("=== fen: %s\n" % fen)
            fh.write("=== lines sent:\n" + "\n".join(">>> " + s for s in script[:-1]) + "\n")
            fh.write("=== stdout:\n" + proc.stdout + "\n=== stderr:\n" + proc.stderr)
            fh.write("=== returncode: %d\n" % proc.returncode)
        accepted = "invalid FEN" not in proc.stdout
        nodes = [ln for ln in proc.stdout.splitlines() if ln.startswith("nodes ")]
        engine_nodes = nodes[0].split()[1] if nodes else "-"
        py, why = perft_py(fen, 3)
        rows.append((i, fen, accepted, engine_nodes, py, why))
    out = os.path.join(outdir, "summary.txt")
    with open(out, "w") as fh:
        for i, fen, acc, en, py, why in rows:
            fh.write("%02d accepted=%-5s engine_perft3=%-8s python_perft3=%-8s (%s)  %s\n"
                     % (i, acc, en, py, why, fen))
    print(open(out).read())


if __name__ == "__main__":
    main()
