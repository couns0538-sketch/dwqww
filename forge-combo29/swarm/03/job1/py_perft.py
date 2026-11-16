#!/usr/bin/env python3
"""py_perft.py FENFILE MAXDEPTH OUTJSON [WORKERS]
python-chess perft 1..MAXDEPTH for each FEN line, multiprocessing; JSON {idx: {d: nodes}} plus any FEN python-chess
refused. Also records, for every position, the legal-move UCI list at the root (for divide comparison)."""
import json, sys, time
import chess
from multiprocessing import Pool

FENFILE, MAXDEPTH, OUTJSON = sys.argv[1], int(sys.argv[2]), sys.argv[3]
W = int(sys.argv[4]) if len(sys.argv) > 4 else 4
fens = [l.strip() for l in open(FENFILE) if l.strip()]

def perft(board, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return board.legal_moves.count()
    n = 0
    for mv in board.legal_moves:
        board.push(mv)
        n += perft(board, depth - 1)
        board.pop()
    return n

def work(arg):
    idx, fen = arg
    b = chess.Board()
    try:
        b.set_fen(fen)
    except Exception as e:  # noqa: BLE001
        return idx, {"refused": str(e)}
    out = {"refused": None, "root_moves": sorted(m.uci() for m in b.legal_moves)}
    for d in range(1, MAXDEPTH + 1):
        out[d] = perft(b, d)
    return idx, out

t0 = time.time()
res = {}
refused = []
with Pool(W) as p:
    for idx, r in p.imap_unordered(work, list(enumerate(fens)), chunksize=8):
        res[str(idx)] = {str(k): v for k, v in r.items()}
        if r["refused"]:
            refused.append([idx, fens[idx], r["refused"]])
        if len(res) % 500 == 0:
            print(f"{len(res)}/{len(fens)} {time.time()-t0:.1f}s", flush=True)
with open(OUTJSON, "w") as f:
    json.dump({"fens": FENFILE, "maxdepth": MAXDEPTH, "results": res, "refused": refused}, f)
print(f"TOTAL {time.time()-t0:.1f}s, refused {len(refused)}")
