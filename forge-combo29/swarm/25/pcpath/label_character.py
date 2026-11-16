#!/usr/bin/env python3
"""label_character.py EXE : characterise the S-F34 failure on the ONE board known to exhibit it.

S-C30 showed a random 40-board sample missed the failure entirely, so a rate is not measurable that way. What IS
measurable is the CHARACTER of the failure on the board that shows it: is the PV short, long, or right-length-but-
not-mate? That decides whether the label advice is "reject by PV length" or "the score is broken".

Uses 4Q3/8/r2K4/... (the S-F33/S-F34 board) across the softnodes budgets where it fails, and classifies each
mate claim. Non-empty by construction, so the conclusion is not about an empty set.
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
BOARDS = ["4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1",
          "7Q/8/8/4K3/8/8/5k2/4R3 w - - 0 1",
          "8/8/4R3/8/7Q/8/1k4K1/8 w - - 0 1"]


def run(fen, go):
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
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, [], 0
    m = re.search(r"score mate (-?\d+)", last)
    d = re.search(r"depth (\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv, (int(d.group(1)) if d else 0)


def classify(fen, mate, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return "illegal-uci"
        if mm not in b.legal_moves:
            return "illegal-move"
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    if b.is_checkmate() and len(pv) == need:
        return "ok"
    if not b.is_checkmate() and len(pv) == need:
        return "RIGHT-LENGTH-NOT-MATE"
    if len(pv) < need:
        return "SHORT"
    return "LONG"


print("### character of the S-F34 failure on the boards that exhibit it")
print(f"{'board':<40} {'budget':<20} {'mate':>5} {'pv':>4} {'need':>5}  class")
counts = {}
for fen in BOARDS:
    for N in (500, 1000, 2000, 5000, 20000):
        mate, pv, depth = run(fen, f"go softnodes {N}")
        if mate is None:
            print(f"{fen[:40]:<40} {'softnodes ' + str(N):<20} {'-':>5} {len(pv):>4} {'-':>5}  (no mate score)")
            continue
        need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
        c = classify(fen, mate, pv)
        counts[c] = counts.get(c, 0) + 1
        print(f"{fen[:40]:<40} {'softnodes ' + str(N):<20} {mate:>5} {len(pv):>4} {need:>5}  {c}")

print()
failures = sum(v for k, v in counts.items() if k != "ok")
print(f"classes: {counts}")
if failures == 0:
    print("NOFAILURES - unmeasured (do not characterise)")
elif counts.get("RIGHT-LENGTH-NOT-MATE", 0) > 0:
    print("VERDICT: at least one failure has the RIGHT PV length but is not mate - the SCORE itself is wrong, so")
    print("rejecting by PV length alone would NOT be sufficient.")
else:
    print("VERDICT: every failure observed here is a SHORT PV - the score is not broken, the REPORT is premature,")
    print("so a pipeline may reject any mate score whose PV length != 2|N|-1 and lose nothing.")
