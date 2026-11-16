#!/usr/bin/env python3
"""perft2cmp.py RESULTS_JSONL EXE — perft 2, engine vs python-chess, for every ACCEPTED case.

The brief's job 2 asks "perft 2 against python-chess where python-chess accepts the FEN".
"""
import json, subprocess, sys, chess

results, exe = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(results)]


def eng_perft(fen, d=2):
    inp = f"uci\nposition fen {fen}\nisready\ngo perft {d}\nquit\n"
    p = subprocess.run([exe], input=inp, capture_output=True, text=True, timeout=120)
    if "invalid FEN" in p.stdout:
        return None
    for line in p.stdout.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def py_perft(b, d):
    if d == 0:
        return 1
    s = 0
    for m in b.legal_moves:
        b.push(m); s += py_perft(b, d - 1); b.pop()
    return s


print(f"{'case':8} {'engine':>8} {'py-chess':>9}  verdict")
diffs = 0
for r in rows:
    fen = r["fen"]
    try:
        b = chess.Board(fen)
        py = py_perft(b, 2)
    except Exception as e:
        print(f"{r['id']:8} {'-':>8} {'py refuses':>9}  (skipped: python-chess rejects)")
        continue
    eng = eng_perft(fen)
    if eng is None:
        print(f"{r['id']:8} {'REFUSED':>8} {py:9d}  (engine refuses, python-chess accepts)")
        continue
    ok = eng == py
    if not ok:
        diffs += 1
    print(f"{r['id']:8} {eng:8d} {py:9d}  {'EQUAL' if ok else '*** DIFFERS ***'}")
print(f"\ndiffering cases: {diffs}")
