#!/usr/bin/env python3
"""remedy_wider.py EXE : does `softnodes 20000` hold up on a WIDER board set than 13?

S-F35 recommends raising self-play to `softnodes 20000` based on 13 boards, and the same file admits a larger
sample is needed for any claim above 20000. The recommendation itself deserves a bigger sample than the anomaly
does, so this repeats the comparison on ~40 mate-rich boards and reports the same two numbers plus a fresh check:
does the self-play move MATCH the move the 250k reference picks? (A label is about the move as much as the score.)

Reference: `go nodes 250000`. Compared: `go softnodes 2000` (current self-play) vs `go softnodes 20000` (proposed).
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
        p.wait(timeout=40)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, [], best
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv, best


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


BOARDS = []
rng = random.Random(2521)
kinds = [[chess.QUEEN], [chess.QUEEN, chess.ROOK], [chess.ROOK, chess.ROOK],
         [chess.QUEEN, chess.BISHOP], [chess.ROOK, chess.BISHOP]]
for _ in range(3000):
    w = list(rng.choice(kinds))
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
    if len(BOARDS) >= 40:
        break

print(f"### S-F35 remedy on a wider set: {len(BOARDS)} mate-rich boards, reference `go nodes 250000`")
print(f"PC r15/PC20, Threads 1, Hash 16")
print()
# PASS 1: the reference answer per board, computed once
ref = {}
for fen in BOARDS:
    ref_num, _, ref_move = run(fen, "go nodes 250000")
    ref[fen] = (ref_num, ref_move)
print(f"reference computed for {len(ref)} boards")
print()

# PASS 2: each budget, compared against the reference
for label, go in (("softnodes 2000 (current)", "go softnodes 2000"),
                  ("softnodes 20000 (proposed)", "go softnodes 20000")):
    mates = bad = diff_num = diff_move = 0
    for fen in BOARDS:
        m, pv, mv = run(fen, go)
        if m is None:
            continue
        mates += 1
        if not ok_pv(fen, m, pv):
            bad += 1
        if m != ref[fen][0]:
            diff_num += 1
        if mv != ref[fen][1]:
            diff_move += 1
    print(f"{label:<30} mate scores {mates:>3} | undeliverable {bad:>2} | number differs {diff_num:>2} "
          f"| MOVE differs {diff_move:>2}")
print()
print("Caveat that must travel with these numbers: 40 purpose-built Q/Q+R/RR/Q+B/R+B vs K endgames, chosen")
print("because mates appear at shallow depth. Worst-case boards, not average play.")
