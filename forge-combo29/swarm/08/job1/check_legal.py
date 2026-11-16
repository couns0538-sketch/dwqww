#!/usr/bin/env python3
"""check_legal.py RAWDIR — every bestmove must be legal in its FEN (python-chess). Prints a table of failures."""
import glob
import json
import os
import sys

import chess

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"
print("| file | searches | illegal or missing bestmove |")
print("|---|---|---|")
total = 0
bad_all = 0
for path in sorted(glob.glob(os.path.join(raw, "*.jsonl"))):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    bad = []
    for r in recs:
        try:
            board = chess.Board(r["fen"])
        except Exception as exc:  # FEN python-chess rejects
            bad.append((r["i"], "FEN rejected by python-chess: %s" % exc))
            continue
        tok = r["bestmove"].split()
        if len(tok) < 2:
            bad.append((r["i"], r["bestmove"]))
            continue
        u = tok[1]
        legal = set()
        for m in board.legal_moves:
            s = board.uci(m)
            legal.add(s)
            # python-chess uci() gives e2e4 form; engine may print promotion the same way
        if legal and u not in legal:
            bad.append((r["i"], u))
    total += len(recs)
    bad_all += len(bad)
    print("| %s | %d | %d |" % (os.path.basename(path), len(recs), len(bad)))
    for i, u in bad:
        print("   - i=%d %s" % (i, u))
print()
print("TOTAL searches %d, bad %d" % (total, bad_all))
