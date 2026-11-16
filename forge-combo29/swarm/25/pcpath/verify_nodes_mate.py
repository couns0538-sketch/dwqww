#!/usr/bin/env python3
"""verify_nodes_mate.py EXE : is the wrong mate score on `go nodes 20000` reproducible?

Found by accident: on 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1 the PC build under PC20 at `go nodes 20000` reports
`mate -7` with a 10-ply PV that python-chess says is NOT checkmate (it needs 14 plies for mate -7). The same
position at `go depth 12` correctly reports mate -4 with an 8-ply PV, and at `go softnodes 20000` correctly
reports mate -4.

`go nodes 20000` is one of the owner's MATCH settings, so a wrong mate label there would corrupt match data.

This checks:
  N1  is it reproducible (5 fresh processes)?
  N2  at several node budgets (5000..250000), how often is the mate score's PV not a mate?
  N3  the control: `go depth 12` on the same board must be correct every time.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"


def run(go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best, depth = None, None, 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    toks = (last or "").split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (m.group(1) if m else None), (int(m.group(2)) if m else None), depth, best, pv


def pv_is_mate(pv, mate):
    b = chess.Board(FEN)
    for i, mv in enumerate(pv):
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return False, f"illegal uci {mv}"
        if m not in b.legal_moves:
            return False, f"illegal {mv}@{i}"
        b.push(m)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    return (b.is_checkmate() and len(pv) == need,
            f"pv {len(pv)} needs {need} mate={b.is_checkmate()}")


print(f"### `go nodes` mate-PV correctness — PC r15/PC20, Threads 1, Hash 16")
print(f"board: {FEN}")
print()
print("N1: five fresh processes at `go nodes 20000`")
for i in range(5):
    k, v, d, bm, pv = run("go nodes 20000")
    if k == "mate":
        ok, why = pv_is_mate(pv, v)
        print(f"  run {i+1}: mate {v:>4} depth {d:>2} move {bm}  {why}  -> {'OK' if ok else 'WRONG'}")
    else:
        print(f"  run {i+1}: {k} {v} depth {d} move {bm} (no mate score)")

print()
print("N2: across node budgets")
for n in (5000, 10000, 20000, 50000, 100000, 250000):
    k, v, d, bm, pv = run(f"go nodes {n}")
    if k == "mate":
        ok, why = pv_is_mate(pv, v)
        print(f"  nodes {n:>7}: mate {v:>4} depth {d:>2}  {why}  -> {'OK' if ok else 'WRONG'}")
    else:
        print(f"  nodes {n:>7}: {k} {v} depth {d} (no mate score)")

print()
print("N3: control, `go depth 12` five times")
bad = 0
for i in range(5):
    k, v, d, bm, pv = run("go depth 12")
    ok, why = pv_is_mate(pv, v) if k == "mate" else (True, "not a mate score")
    bad += (not ok)
    print(f"  run {i+1}: mate {v} depth {d}  {why}  -> {'OK' if ok else 'WRONG'}")
print()
print(f"control wrong count: {bad}/5  (must be 0 for the node-limit result to be meaningful)")
