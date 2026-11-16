#!/usr/bin/env python3
"""nodes_mate_survey.py EXE FENS N : how often does `go nodes 20000` produce a mate score whose PV is not a mate?

The rate is what decides severity. For each position: `go nodes 20000`, and if the score is `mate N`, play the
PV with python-chess and check it is checkmate at exactly 2N-1 (or 2|N|) plies.

Controls (Rule 1):
  * `go depth 12` on the same positions must yield 0 wrong mate PVs (the harness can verify a mate) - if the
    control shows wrongs, the survey is measuring my checker, not the engine.
  * the count of mate scores seen must be > 0, otherwise "0 wrong" would be vacuous.
"""
import json
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
FENS = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 60


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


def check(fen, mate, pv):
    """True if the PV is a mate at the claimed distance."""
    b = chess.Board(fen)
    for i, mv in enumerate(pv):
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return False, f"illegal uci {mv}"
        if m not in b.legal_moves:
            return False, f"illegal {mv}@{i}"
        b.push(m)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    if b.is_checkmate() and len(pv) == need:
        return True, f"ok {len(pv)}/{need}"
    return False, f"pv {len(pv)} need {need} mate={b.is_checkmate()}"


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print(f"### survey: `go nodes 20000` mate PVs — PC r15/PC20, Threads 1, Hash 16, {len(fens)} positions")
report = {}
for label, go in (("nodes 20000", "go nodes 20000"), ("CONTROL depth 12", "go depth 12")):
    mates = wrong = 0
    bad_rows = []
    for fen in fens:
        b = chess.Board(fen)
        if b.is_game_over(claim_draw=False):
            continue
        k, v, d, bm, pv = run(fen, go)
        if k != "mate" or v is None:
            continue
        mates += 1
        ok, why = check(fen, v, pv)
        if not ok:
            wrong += 1
            bad_rows.append((fen, v, d, pv, why))
    report[label] = (mates, wrong, bad_rows)
    verdict = "" if mates > 0 else "  <-- VACUOUS: no mate scores at all"
    print(f"{label:<20} mate scores {mates:>3}  wrong PV {wrong:>3}{verdict}")
    for fen, v, d, pv, why in bad_rows[:5]:
        print(f"    WRONG mate {v:>4} depth {d:>2} {fen[:44]}  {why}")

nm, nw, _ = report["nodes 20000"]
cm, cw, _ = report["CONTROL depth 12"]
print()
if cm == 0:
    print("CONTROL VACUOUS: depth 12 produced no mate scores, so this survey proves nothing about my checker.")
elif cw > 0:
    print(f"CONTROL FAILED: the checker reports {cw} wrong mate PVs at depth 12, so it (or the engine there) is at fault.")
    print("The nodes-20000 count is NOT a result until the control is clean.")
else:
    print(f"CONTROL CLEAN: depth 12 gave {cm} mate scores and 0 wrong PVs, so the checker can verify a mate.")
    if nm == 0:
        print("But `go nodes 20000` produced no mate scores in this sample, so its rate is unmeasured here.")
    else:
        print(f"RESULT: at `go nodes 20000`, {nw} of {nm} mate scores have a PV that is not a mate "
              f"({100.0*nw/nm:.1f}%).")
