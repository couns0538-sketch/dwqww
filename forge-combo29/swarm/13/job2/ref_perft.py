#!/usr/bin/env python3
"""Reference side of area 3 job 1: perft 1..4 with python-chess, split per root move.

Also records, for every difference at depth<=2, the root-move divide on both sides so the
difference can be localised without a second run.
Usage: ref_perft.py FENS OUT DEPTHS
"""
import sys
import time

import chess


def perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        n = 0
        for _ in board.generate_legal_moves():
            n += 1
        return n
    n = 0
    for m in board.generate_legal_moves():
        board.push(m)
        n += perft(board, depth - 1)
        board.pop()
    return n


def divide(board, depth):
    d = {}
    if depth == 0:
        return d
    for m in board.generate_legal_moves():
        board.push(m)
        d[m.uci()] = perft(board, depth - 1)
        board.pop()
    return d


def main():
    fens = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    out_path = sys.argv[2]
    depths = [int(x) for x in sys.argv[3].split(",")]
    out = open(out_path, "w")
    out.write("# idx depth nodes marker\n")
    t0 = time.monotonic()
    boards = []
    for idx, fen in enumerate(fens):
        try:
            b = chess.Board(fen)
            valid = b.is_valid() or True  # python-chess parses it; record validity separately
            boards.append(b)
            mark = "OK" if b.status() == chess.STATUS_VALID else "PYCC_INVALID"
        except ValueError:
            boards.append(None)
            out.write(" ".join(f"{idx} {d} ERR INVALID_FEN" for d in depths) + "\n")
            continue
        for d in depths:
            n = perft(b, d)
            out.write(f"{idx} {d} {n} {mark}\n")
        if idx % 250 == 0:
            out.flush()
            print("ref", idx, round(time.monotonic() - t0, 1), "s", flush=True)
    out.close()
    print("ref done", len(fens), round(time.monotonic() - t0, 1), "s")


main()
