#!/usr/bin/env python3
"""lr_configs.py EXE FENS : left-right differences per eval configuration.

Runs the same left-right comparison under three configurations so the cause can be separated:
  default        hce + nnue
  nonnue         hce only (UseNNUE false, nnue reads 0)
  nonnue_dead    hce only with DeadMaterial true
Prints, per configuration, how many positions differ and the median |delta total|.
"""
import statistics
import subprocess
import sys

import chess
import mirror_lr as M

EXE, FENS = sys.argv[1], sys.argv[2]
CONFIGS = {"default": [], "nonnue": [("UseNNUE", "false")],
           "nonnue_deadmat": [("UseNNUE", "false"), ("DeadMaterial", "true")]}


class Eng(M.Engine):
    def __init__(self, exe, opts):
        super().__init__(exe)
        for name, val in opts:
            self.send(f"setoption name {name} value {val}")
            self.send("isready")
            self.check(self.read_until())


fens = [l.strip() for l in open(FENS) if l.strip()]
for cfg, opts in CONFIGS.items():
    eng = Eng(EXE, opts)
    n = diff = 0
    deltas = []
    hce_only = nnue_only = both = 0
    for fen in fens:
        lr = chess.Board(fen).transform(chess.flip_horizontal).fen()
        a, b = M.parse(eng.ev(fen)), M.parse(eng.ev(lr))
        n += 1
        d = [k for k in ("hce", "nnue", "total") if a[k] != b[k]]
        if d:
            diff += 1
            deltas.append(abs(a["total"] - b["total"]))
            if "hce" in d:
                hce_only += 1
            if "nnue" in d:
                nnue_only += 1
    eng.quit()
    med = statistics.median(deltas) if deltas else 0
    print(f"{cfg:16s} positions {n:4d} differ_total {diff:4d}  hce_differs {hce_only:4d} "
          f"nnue_differs {nnue_only:4d}  median|dtotal| {med}")
