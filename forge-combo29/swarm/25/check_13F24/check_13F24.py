#!/usr/bin/env python3
"""check_13F24.py EXE : independent check of seat 13's CORRECTED S-F24.

THE CLAIM (their corrected version, which I am checking):
  With a FRESH PROCESS PER SEARCH, over 16 G positions at a 2,000 ms vs a 60,000 ms clock
  (PC20, Threads 1, Hash 16), only ONE position changes its move with the clock, and there the longer
  clock's move is better by +17 cp at equal depth 16. Median depth 15 at 2 s, 23 at 60 s.

WHY IT NEEDS A SECOND PAIR OF EYES: their FIRST version of this finding was contaminated by reusing one engine
process across searches (warm TT shifted scores up to 80 cp on identical requests). They withdrew it and re-ran
with fresh processes. The question for me: does the corrected number hold, or is one-per-process still not enough?

MY HARNESS, written independently from their claim (not a copy of their script):
  * one FRESH PROCESS PER SEARCH - never reused, which is the discipline their correction depends on
  * their 16 FENs, read from their own G_all.fens selection (committed in their job20/out_fresh json)
  * their settings: PC20 (14 S14 options + 6 PC options), Threads 1, Hash 16
  * a 2000 ms clock and a 60000 ms clock
  * then, for BOTH candidate moves, a score at FIXED DEPTH 16 (their judging depth) so the comparison is at
    equal depth rather than at each clock's own depth - a fresh process for each of those too

Reports: how many positions change move, and the depth-16 score of each candidate.
"""
import json
import re
import shlex
import subprocess
import sys
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FENS_FILE = sys.argv[2]
JUDGE_DEPTH = 16

# the 16 FENs seat 13 used, in their order (line numbers into G_all.fens, 1-based)
THEIR_ROWS = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16


def spawn():
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return True
        return False

    def send(cmd):
        p.stdin.write(cmd + "\n"); p.stdin.flush()

    send("uci"); until("uciok")
    send("setoption name Threads value 1"); send("isready"); until("readyok")
    send("setoption name Hash value 16"); send("isready"); until("readyok")
    for n, v in S14 + PC20:
        send(f"setoption name {n} value {v}")
    send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    return p, send, until


def search(fen, go):
    """One search in a FRESH process. Returns dict(bestmove, depth, nodes, cp, mate)."""
    p, send, until = spawn()
    send(f"position fen {fen}"); send("isready"); until("readyok")
    t0 = time.monotonic()
    send(go)
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
    elapsed = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    depth = nodes = cp = mate = None
    if last:
        d = re.search(r"depth (\d+)", last)
        depth = int(d.group(1)) if d else None
        n = re.search(r"nodes (\d+)", last)
        nodes = int(n.group(1)) if n else None
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        if m:
            if m.group(1) == "cp":
                cp = int(m.group(2))
            else:
                mate = int(m.group(2))
    return {"bestmove": best, "depth": depth, "nodes": nodes, "cp": cp, "mate": mate,
            "ms": round(elapsed)}


def score_move_at_depth(fen, move, depth=JUDGE_DEPTH):
    """Score of a SPECIFIC move, by playing it and searching the reply at fixed depth, fresh process.

    Returns the score from the ORIGINAL side's point of view (negated, since the reply is the opponent's).
    """
    b = chess.Board(fen)
    try:
        mv = chess.Move.from_uci(move)
    except ValueError:
        return None
    if mv not in b.legal_moves:
        return None
    b.push(mv)
    r = search(b.fen(), f"go depth {depth}")
    if r["mate"] is not None:
        # a mate for the opponent is a loss for us
        return None if r["mate"] > 0 else None
    if r["cp"] is None:
        return None
    return -r["cp"]


fens = [l.strip() for l in open(FENS_FILE) if l.strip()]
sel = [fens[i - 1] for i in THEIR_ROWS if i - 1 < len(fens)]
print(f"### independent check of seat 13's corrected S-F24")
print(f"exe {EXE}")
print(f"positions: {len(sel)} | clocks: 2000 ms vs 60000 ms | PC20, Threads 1, Hash 16 | fresh process per search")
print(f"judging depth for the candidate comparison: {JUDGE_DEPTH}")
print()
print(f"{'pos':>3} {'short mv':>8} {'d':>3} {'cp':>6} | {'long mv':>8} {'d':>3} {'cp':>6} | {'same':>5}  {'gap@d16':>8}")
changed = []
for idx, fen in enumerate(sel, 1):
    s = search(fen, "go wtime 2000 btime 2000 winc 0 binc 0")
    l = search(fen, "go wtime 60000 btime 60000 winc 0 binc 0")
    same = s["bestmove"] == l["bestmove"]
    gap = ""
    if not same:
        ssc = score_move_at_depth(fen, s["bestmove"])
        lsc = score_move_at_depth(fen, l["bestmove"])
        if ssc is not None and lsc is not None:
            gap = f"{lsc - ssc:+d}"
            changed.append((idx, s["bestmove"], l["bestmove"], ssc, lsc, lsc - ssc))
        else:
            changed.append((idx, s["bestmove"], l["bestmove"], ssc, lsc, None))
    print(f"{idx:>3} {str(s['bestmove']):>8} {str(s['depth']):>3} {str(s['cp']):>6} | "
          f"{str(l['bestmove']):>8} {str(l['depth']):>3} {str(l['cp']):>6} | {str(same):>5}  {gap:>8}")

print()
print(f"positions changing move: {len(changed)} of {len(sel)}")
for idx, sm, lm, ssc, lsc, g in changed:
    print(f"  pos {idx}: short {sm} (d16 {ssc}) -> long {lm} (d16 {lsc})   gap {g:+d}" if g is not None
          else f"  pos {idx}: short {sm} -> long {lm}   (gap not computable)")
print()
print("SEAT 13's CORRECTED CLAIM: 1 of 16 changes move, and that one is +17 cp better on the longer clock.")
print(f"MY RESULT: {len(changed)} of {len(sel)} change move."
      + (f" Gaps: {[c[5] for c in changed if c[5] is not None]}." if changed else ""))
