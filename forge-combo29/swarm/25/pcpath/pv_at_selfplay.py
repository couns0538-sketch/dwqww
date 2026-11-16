#!/usr/bin/env python3
"""pv_at_selfplay.py EXE FENS N : my area-5 core check at the setting that produces training labels.

My job 1 checked PV legality at depth 12 (S14, base tree). The owner's SELF-PLAY labels come from
`go softnodes 2000` on the PC build under PC20. So the question that actually matters for training data is:
at the depth softnodes reaches (~7-8), is the final PV legal, and is any mate score consistent with its PV?

This runs the check on the self-play setting and also at `go nodes 20000` (the match setting) for contrast.
PVs are SLICED from the engine's own info lines, never typed (the COPYING_RULE discipline).
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
EXE, FENS = sys.argv[1], sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 100
GOS = [("softnodes 2000 (SELF-PLAY)", "go softnodes 2000"),
       ("nodes 20000 (MATCH)", "go nodes 20000")]


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
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, None, best, 0
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    return (m.group(0) if m else None), pv, best, len(pv)


def check_pv(fen, pv):
    b = chess.Board(fen)
    for i, mv in enumerate(pv):
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False, f"bad uci {mv}"
        if mm not in b.legal_moves:
            return False, f"illegal {mv}@{i}"
        b.push(mm)
    return True, "ok"


def check_mate(fen, score, pv):
    m = re.match(r"score mate (-?\d+)", score or "")
    if not m:
        return True, "not a mate score"
    v = int(m.group(1))
    need = 2 * v - 1 if v > 0 else 2 * abs(v)
    b = chess.Board(fen)
    for mv in pv:
        mm = chess.Move.from_uci(mv)
        if mm not in b.legal_moves:
            return False, "illegal in mate pv"
        b.push(mm)
    return (b.is_checkmate() and len(pv) == need), f"pv {len(pv)} need {need} mate={b.is_checkmate()}"


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print(f"### area-5 core check at the settings that PRODUCE LABELS — PC r15/PC20, Threads 1, Hash 16")
print(f"positions: {len(fens)} (set G)")
for label, go in GOS:
    illegal = mate_bad = mates = nopv = 0
    for fen in fens:
        b = chess.Board(fen)
        if b.is_game_over(claim_draw=False):
            continue
        score, pv, best, pvlen = run(fen, go)
        if pv is None:
            nopv += 1
            continue
        ok, why = check_pv(fen, pv)
        if not ok:
            illegal += 1
        mok, mwhy = check_mate(fen, score, pv)
        if score and "mate" in score:
            mates += 1
            if not mok:
                mate_bad += 1
    print(f"  {label:<28} illegal PVs {illegal:>3} | mate scores {mates:>3} | mate PVs wrong {mate_bad:>3} "
          f"| positions with no pv {nopv:>3}")
