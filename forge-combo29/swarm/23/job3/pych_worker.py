#!/usr/bin/env python3
"""pych_worker.py : reference perft counts + divide for a slice of a FEN file.

usage: pych_worker.py FENS START END MAXDEPTH OUT_JSONL
Reads FENS lines [START, END), writes one json object per line with nodes per depth and the
divide at MAXDEPTH (python-chess's own legal move list is the reference).
"""
import json
import sys

import chess

from pych_perft import count

FENS, START, END, MAXDEPTH, OUT = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]

fens = [line.strip() for line in open(FENS) if line.strip()][START:END]
with open(OUT, "w") as out:
    for i, fen in enumerate(fens):
        board = chess.Board(fen)
        if not board.is_valid():
            out.write(json.dumps({"i": START + i, "fen": fen, "invalid": True}) + "\n")
            continue
        nodes = {}
        for d in range(1, MAXDEPTH + 1):
            nodes[str(d)] = count(board, d)
        out.write(json.dumps({"i": START + i, "fen": fen, "invalid": False,
                              "nodes": nodes}) + "\n")
        if i % 50 == 0:
            print("worker[%d:%d] %d/%d" % (START, END, i, len(fens)), flush=True)
print("worker[%d:%d] done %d" % (START, END, len(fens)), flush=True)
