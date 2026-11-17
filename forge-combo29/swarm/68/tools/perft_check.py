#!/usr/bin/env python3
"""Movegen validation for the independent verifier.

Two references, both external to the verifier:

  1. Published perft values (the standard Kiwipete / position-3/4/5/6 set).
     These catch gross generator faults and exercise castling rights, en
     passant, promotions, pins and checks.
  2. python-chess perft over the SAME positions and a set of random-walk
     endgame positions. This is the load-bearing check: it is an independent
     implementation, so agreement is evidence rather than a restatement of a
     number typed from memory.

An expectation typed from memory is itself a fixture that can be wrong: an
earlier version of this file asserted 89879 for position 6 at depth 3 and the
verifier was blamed for returning 89890. python-chess returns 89890. The
published table was the thing that was wrong here, which is why reference (2)
exists and why the published table is cross-checked against it below.

Every count prints numerator and denominator as literals.
"""
import random
import subprocess
import sys

import chess

HERE = __file__.rsplit("/", 1)[0]
VERIFY = HERE + "/mateverify"

PUBLISHED = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5, 4865609),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 4, 4085603),
    ("position3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5, 674624),
    ("position4w", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 4, 422333),
    ("position4b", "r2q1rk1/pP1p2pp/Q4n2/bbp1p3/Np6/1B3NBn/pPPP1PPP/R3K2R b KQ - 0 1", 4, 422333),
    ("position5", "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", 4, 2103487),
    ("position6", "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", 3, 89890),
]

# Endgame/small-board positions where promotions and en passant are frequent.
EXTRA_FENS = [
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "8/P1k5/8/8/8/8/5K1p/8 w - - 0 1",
    "4k3/8/8/8/8/8/8/4K2R w K - 0 1",
    "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "8/8/8/8/8/8/6p1/4K2k b - - 0 1",
    "4k3/8/8/2pP4/8/8/8/4K3 w - c6 0 1",
    "8/8/8/8/8/5k2/6p1/6K1 b - - 0 1",
    "n1n5/PPPk4/8/8/8/8/4Kppp/5N1N b - - 0 1",
]


def mine_perft(fen, depth):
    r = subprocess.run([VERIFY, "--perft", str(depth), fen], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return int(r.stdout.strip())


def py_perft(board, depth):
    if depth == 0:
        return 1
    total = 0
    for mv in board.legal_moves:
        board.push(mv)
        total += py_perft(board, depth - 1)
        board.pop()
    return total


def random_walk_fens(n, plies, rng):
    """Endgame-ish FENs from random legal play, biased toward sparse boards."""
    out = []
    while len(out) < n:
        b = chess.Board()
        for _ in range(plies):
            if b.is_game_over():
                break
            b.push(rng.choice(list(b.legal_moves)))
        if b.is_game_over():
            continue
        out.append(b.fen())
    return out


def main():
    rng = random.Random(6801)
    bad = 0

    print("A. Published perft table (cross-checked against python-chess)")
    print(f"{'case':12s} {'depth':>5s} {'verifier':>10s} {'python-chess':>13s} {'published':>10s}  verdict")
    for name, fen, depth, expected in PUBLISHED:
        got = mine_perft(fen, depth)
        pyv = py_perft(chess.Board(fen), depth)
        ok = got == pyv == expected
        if not ok:
            bad += 1
        note = "ok" if ok else ("FAIL: published table disagrees with python-chess" if pyv != expected
                                else "FAIL: verifier disagrees")
        print(f"{name:12s} {depth:5d} {got if got is not None else -1:10d} {pyv:13d} {expected:10d}  {note}")

    print("\nB. python-chess agreement on hand-picked and random endgames")
    fens = list(EXTRA_FENS) + random_walk_fens(12, 60, rng)
    print(f"{'#':>3s} {'depth':>5s} {'verifier':>10s} {'python-chess':>13s}  verdict")
    for i, fen in enumerate(fens):
        depth = 3 if i < len(EXTRA_FENS) else 2
        got = mine_perft(fen, depth)
        pyv = py_perft(chess.Board(fen), depth)
        ok = got == pyv
        if not ok:
            bad += 1
        print(f"{i:3d} {depth:5d} {got if got is not None else -1:10d} {pyv:13d}  {'ok' if ok else 'FAIL'}")
        if not ok:
            print(f"     fen: {fen}")

    total = len(PUBLISHED) + len(fens)
    print(f"\n{total - bad}/{total} perft cases agree")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
