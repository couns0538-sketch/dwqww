#!/usr/bin/env python3
"""mate_under_selfplay.py EXE : do my mate findings matter at the owner's SELF-PLAY setting?

S-F1 and S-F8 were wrong mate scores at depth 12. The PC build repairs them at depth 12 under PC20, but the
owner's self-play does not use depth 12 - it uses `go softnodes 2000`, which stops at a FINISHED depth around
7-8. So the question that matters for training labels is: at the depth self-play actually reaches, does the
engine report a mate score at all, and is it right?

For each of my two mate boards:
  * `go softnodes 2000` (self-play) -> score, depth reached, PV length
  * if it reports a mate, verify the PV with python-chess (legal? checkmate? as many plies as claimed?)
  * and `go softnodes 20000` / `go nodes 20000` for the match settings
This says whether a training label from self-play would be corrupted by a wrong mate number.
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
BOARDS = [
    ("S-F1 (was mate -12 at d12 on base)", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("S-F8 (was mate -9 at d12 on base)", "2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22"),
]
GOS = ["go softnodes 2000", "go softnodes 20000", "go nodes 20000", "go depth 12"]


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


def verify(fen, pv, mate):
    if mate is None or mate == 0:
        return "n/a (not a mate score)"
    b = chess.Board(fen)
    for i, mv in enumerate(pv):
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return f"ILLEGAL uci {mv} at {i}"
        if m not in b.legal_moves:
            return f"ILLEGAL {mv} at ply {i}"
        b.push(m)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    is_mate = b.is_checkmate()
    ok = is_mate and len(pv) == need
    return (f"{'CORRECT' if ok else 'WRONG'}: pv {len(pv)} plies, needs {need}, checkmate={is_mate}")


print(f"### mate findings at the owner's self-play setting — PC r15/PC20, Threads 1, Hash 16")
for name, fen in BOARDS:
    print("=" * 78)
    print(f"{name}")
    print(f"  {fen}")
    for go in GOS:
        k, v, d, bm, pv = run(fen, go)
        print(f"  {go:<22} {str(k) + ' ' + str(v):>12}  depth {d:>2}  pv {len(pv):>2}  move {bm}")
        if k == "mate":
            print(f"      PV check: {verify(fen, pv, v)}")
