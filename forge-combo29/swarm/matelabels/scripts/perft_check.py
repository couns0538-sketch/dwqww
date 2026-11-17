#!/usr/bin/env python3
"""Validate the independent oracle's move generator against published perft values.

Perft is the only cheap test that exercises castling, en passant, promotion and
pins at once. If these numbers do not match, the oracle's mate answers mean
nothing.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chess
import paths

ORACLE = paths.oracle_binary()

# Published perft values (CPW / standard positions).
CASES = [
    ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "startpos", [1, 2, 3, 4, 5],
     [20, 400, 8902, 197281, 4865609]),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "kiwipete", [1, 2, 3, 4],
     [48, 2039, 97862, 4085603]),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "pos3", [1, 2, 3, 4, 5],
     [14, 191, 2812, 43238, 674624]),
    ("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", "pos4", [1, 2, 3, 4],
     [6, 264, 9467, 422333]),
    ("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8", "pos5", [1, 2, 3, 4],
     [44, 1486, 62379, 2103487]),
    ("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10", "pos6", [1, 2, 3],
     [46, 2079, 89890]),
]


def py_perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    total = 0
    for move in board.legal_moves:
        board.push(move)
        total += py_perft(board, depth - 1)
        board.pop()
    return total


def run_oracle(fen, depth):
    out = subprocess.run([ORACLE, "perft", fen, str(depth)], capture_output=True, text=True)
    line = out.stdout.strip().split("\n")[-1]
    if not line.startswith("PERFT"):
        return None
    return int(line.split()[2])


def main():
    rows = []
    ok_all = True
    for fen, name, depths, expected in CASES:
        for depth, exp in zip(depths, expected):
            got = run_oracle(fen, depth)
            # Cross-check the same position/depth with python-chess, an
            # independent implementation, so a mismatch tells us which engine
            # is wrong rather than that two implementations disagree.
            b = chess.Board(fen)
            py = py_perft(b, depth)
            match_pub = (got == exp)
            match_py = (got == py)
            ok_all &= match_pub and match_py
            rows.append({
                "position": name, "fen": fen, "depth": depth,
                "oracle": got, "published": exp, "python_chess": py,
                "match_published": match_pub, "match_python_chess": match_py,
            })
            status = "OK" if (match_pub and match_py) else "MISMATCH"
            print(f"{status:9} {name:10} d{depth}  oracle={got}  published={exp}  python={py}")

    print()
    print("ALL PERFT MATCH" if ok_all else "PERFT FAILURE — oracle is not trustworthy")
    with open(paths.work_file("perft.json"), "w") as f:
        json.dump({"all_match": ok_all, "rows": rows}, f, indent=1)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
