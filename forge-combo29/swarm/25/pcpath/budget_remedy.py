#!/usr/bin/env python3
"""budget_remedy.py EXE : does raising the self-play budget FIX the two label problems?

S-F34 measured two faults at `go softnodes 2000`: 1/13 mate PVs undeliverable and 3/13 mate numbers one move
pessimistic. The obvious remedy is a bigger budget - but which one, and does it work? This sweeps the budget and
reports, per budget: how many mate scores, how many undeliverable PVs, and how many differ from the
`go nodes 250000` reference (which is the most-converged answer I can afford).

That gives the owner a concrete recommendation ("use N >= X") instead of "raise it somehow".
"""
import random
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
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, [], 0
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv, len(pv)


def ok_pv(fen, mate, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False
        if mm not in b.legal_moves:
            return False
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    return b.is_checkmate() and len(pv) == need


BOARDS = ["4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1",
          "7Q/8/8/4K3/8/8/5k2/4R3 w - - 0 1",
          "8/8/4R3/8/7Q/8/1k4K1/8 w - - 0 1"]
rng = random.Random(2521)
kinds = [[chess.QUEEN], [chess.QUEEN, chess.ROOK], [chess.ROOK, chess.ROOK], [chess.QUEEN, chess.BISHOP]]
for _ in range(200):
    w = rng.choice(kinds)
    sqs = rng.sample(range(64), 2 + len(w))
    b = chess.Board(None)
    b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
    for i, pt in enumerate(w):
        b.set_piece_at(sqs[2 + i], chess.Piece(pt, chess.WHITE))
    b.turn = chess.WHITE
    b.clear_stack()
    if b.is_valid() and not b.is_game_over(claim_draw=False) and not b.is_insufficient_material():
        f = b.fen()
        if f not in BOARDS:
            BOARDS.append(f)
    if len(BOARDS) >= 13:
        break

print(f"### does a bigger self-play budget fix the two label faults? ({len(BOARDS)} mate-rich boards)")
print("reference = `go nodes 250000`; a board 'differs' if its mate number is not the reference's")
print()
BUDGETS = ["go softnodes 2000", "go softnodes 20000", "go softnodes 50000",
           "go nodes 20000", "go nodes 50000", "go nodes 250000"]
ref = {}
for fen in BOARDS:
    m, pv, _ = run(fen, "go nodes 250000")
    ref[fen] = m
print(f"{'budget':<24} {'mate scores':>11} {'undeliverable':>14} {'differs from 250k':>18}")
for go in BUDGETS:
    n = bad = diff = 0
    for fen in BOARDS:
        m, pv, _ = run(fen, go)
        if m is None:
            continue
        n += 1
        if not ok_pv(fen, m, pv):
            bad += 1
        if m != ref[fen]:
            diff += 1
    print(f"{go:<24} {n:>11} {bad:>14} {diff:>18}")
