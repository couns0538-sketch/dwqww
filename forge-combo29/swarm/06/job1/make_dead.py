#!/usr/bin/env python3
"""Dead-material positions for the mirror check (area 6 job 1, extra path).

Builds every legal-ish combination the engine's dead_material_score() can act on, in both colours,
and writes them so the mirror harness compares each with its colour-flipped mirror.
"""
import sys

import chess

out = sys.argv[1]
cands = [
    # K v K
    "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/4K3 b - - 0 1",
    # KN v K, both colours, knight in various corners
    "4k3/8/8/8/8/8/8/N3K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/n3K3 b - - 0 1",
    "4k3/8/8/8/8/8/8/3NK3 w - - 0 1",
    "3nk3/8/8/8/8/8/8/4K3 b - - 0 1",
    # KB v K on a dark and on a light square, both colours
    "4k3/8/8/8/8/8/8/B3K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/b3K3 b - - 0 1",
    "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/2b1K3 b - - 0 1",
    # KNN v K
    "4k3/8/8/8/8/8/8/NN2K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/nn2K3 b - - 0 1",
    # KN+B v K (the corner-driving path)
    "4k3/8/8/8/8/8/8/NB2K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/nb2K3 b - - 0 1",
    "4k3/8/8/8/8/8/8/BN2K3 w - - 0 1",
    "4k3/8/8/8/8/8/8/bn2K3 b - - 0 1",
    # the pair path with the lone king in every corner
    "k7/8/8/8/8/8/8/NB2K3 w - - 0 1",
    "k7/8/8/8/8/8/8/NB2K3 b - - 0 1",
    "7k/8/8/8/8/8/8/NB2K3 w - - 0 1",
    "7k/8/8/8/8/8/8/NB2K3 b - - 0 1",
    "8/8/8/8/8/8/8/NB2K2k w - - 0 1",
    "8/8/8/8/8/8/8/NB2K2k b - - 0 1",
    # light-squared bishop pair (the other corner set)
    "k7/8/8/8/8/8/8/BN2K3 w - - 0 1",
    "k7/8/8/8/8/8/8/BN2K3 b - - 0 1",
    # pair with the kings far apart and close, to exercise the drive term
    "k7/8/8/8/8/8/6K1/NB6 w - - 0 1",
    "k7/8/8/8/8/8/6K1/NB6 b - - 0 1",
    # black is the pair side
    "nb2k3/8/8/8/8/8/8/K7 w - - 0 1",
    "nb2k3/8/8/8/8/8/8/K7 b - - 0 1",
    # fifty-move clock, same material
    "4k3/8/8/8/8/8/8/NB2K3 w - - 99 120",
    "4k3/8/8/8/8/8/8/NB2K3 b - - 99 120",
]

kept = []
for fen in cands:
    try:
        b = chess.Board(fen)
    except Exception as exc:
        print("SKIP (python-chess): %s -> %s" % (fen, exc))
        continue
    if not b.is_valid():
        print("SKIP (invalid): %s status=%s" % (fen, b.status()))
        continue
    kept.append(fen)

with open(out, "w") as fh:
    for fen in kept:
        fh.write(fen + "\n")
print("kept=%d of %d" % (len(kept), len(cands)))
