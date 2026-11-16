#!/usr/bin/env python3
"""match_game.py EXE : play a full self-play game at the owner's MATCH settings and audit every move.

The owner's matches use PC20, Threads 1, Hash 16, `go nodes 20000`. This plays the engine against itself for a
full game at exactly that setting and audits each move:
  * is the bestmove legal?                      (an illegal move would end everything)
  * was it chosen from a COMPLETED iteration?   (every final info line should carry a pv)
  * how many nodes did it actually spend vs 20000? (the S-C12 budget-ratio question, on a real game)
  * does the game terminate normally (mate / repetition / 50-move / insufficient)?
That is the closest thing to the owner's actual usage that I can run, and it exercises every code path at once.
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
MAXPLY = int(sys.argv[2]) if len(sys.argv) > 2 else 200
NODES = 20000


def ask(fen, go=f"go nodes {NODES}"):
    """One fresh process per move: the engine's normal match usage."""
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
        if s.startswith("info depth"):
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
    nodes = None
    pvlen = 0
    if last:
        n = re.search(r"nodes (\d+)", last)
        nodes = int(n.group(1)) if n else None
        toks = last.split()
        pvlen = len(toks[toks.index("pv") + 1:]) if "pv" in toks else 0
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        score = m.group(0) if m else "?"
    else:
        score = "NO-INFO"
    return best, depth, nodes, pvlen, score, last


b = chess.Board()
rows = []
illegal = no_info = completed = 0
node_ratios = []
for ply in range(MAXPLY):
    if b.is_game_over(claim_draw=True):
        break
    best, depth, nodes, pvlen, score, last = ask(b.fen())
    legal = False
    if best and best != "0000":
        try:
            mv = chess.Move.from_uci(best)
            legal = mv in b.legal_moves
        except ValueError:
            legal = False
    if not legal:
        illegal += 1
        rows.append((ply, b.fen(), best, depth, nodes, pvlen, score, "ILLEGAL/0000"))
        break
    if last is None:
        no_info += 1
    if pvlen > 0:
        completed += 1
    if nodes is not None:
        node_ratios.append(nodes / NODES)
    rows.append((ply, b.fen(), best, depth, nodes, pvlen, score, ""))
    b.push(chess.Move.from_uci(best))

print(f"### self-play at the owner's match setting — PC r15/PC20, Threads 1, Hash 16, {NODES} nodes/move")
print(f"plies played: {len(rows)}")
print(f"game result: {b.outcome(claim_draw=True)}")
print(f"illegal moves / no legal move: {illegal}")
print(f"moves whose final info line was missing: {no_info}")
print(f"moves with a non-empty PV in the final line: {completed}/{len(rows)}")
if node_ratios:
    import statistics
    print(f"nodes actually spent / {NODES}: median {statistics.median(node_ratios):.2f}, "
          f"min {min(node_ratios):.2f}, max {max(node_ratios):.2f}")
print()
print(f"{'ply':>4} {'move':>6} {'depth':>6} {'nodes':>7} {'pv':>3} {'score':>12}  flag")
for ply, fen, best, depth, nodes, pvlen, score, flag in rows:
    if flag or ply < 6 or ply > len(rows) - 5:
        print(f"{ply:>4} {str(best):>6} {depth:>6} {str(nodes):>7} {pvlen:>3} {score:>12}  {flag}")
