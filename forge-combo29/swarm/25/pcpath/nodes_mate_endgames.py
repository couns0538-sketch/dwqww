#!/usr/bin/env python3
"""nodes_mate_endgames.py EXE : the rate of S-F27's fault on boards where mates ARE frequent at 20k nodes.

The middlegame survey was vacuous (1 mate score in 100). This uses positions built so that a forced mate exists
and is findable at a small node budget: KQ vs K, KR vs K, QR vs K, and my S-F1 board. For each, at
`go nodes 20000`:
  * is the score a mate?
  * is its PV a mate at the claimed distance?
and the SAME at `go depth 12` as the control.

If the fault rate is high here, S-F27 is serious for endgame match data. If it is 0, then S-F27 is a rare
mid-iteration artefact and its severity is limited - either answer is useful and I will report which.
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
    return (b.is_checkmate() and len(pv) == need,
            f"pv {len(pv)} need {need} mate={b.is_checkmate()}")


BOARDS = ["8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"]
rng = random.Random(2521)
# KQ/KR/QR vs K: white to move, a mate exists at some distance
kinds = [[chess.QUEEN], [chess.ROOK], [chess.QUEEN, chess.ROOK], [chess.ROOK, chess.ROOK]]
for _ in range(120):
    w = rng.choice(kinds)
    sqs = rng.sample(range(64), 2 + len(w))
    b = chess.Board(None)
    b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
    for i, pt in enumerate(w):
        b.set_piece_at(sqs[2 + i], chess.Piece(pt, chess.WHITE))
    b.turn = chess.WHITE
    b.clear_stack()
    if b.is_valid() and not b.is_game_over(claim_draw=False):
        f = b.fen()
        if f not in BOARDS:
            BOARDS.append(f)
    if len(BOARDS) >= 41:
        break

print(f"### S-F27 rate on boards where mates are frequent at 20k nodes ({len(BOARDS)} boards)")
print("PC r15/PC20, Threads 1, Hash 16")
for label, go in (("nodes 20000", "go nodes 20000"), ("CONTROL depth 12", "go depth 12")):
    mates = wrong = 0
    rows = []
    for fen in BOARDS:
        k, v, d, bm, pv = run(fen, go)
        if k != "mate" or v is None:
            continue
        mates += 1
        ok, why = check(fen, v, pv)
        if not ok:
            wrong += 1
            rows.append((fen, v, d, why))
    print(f"{label:<20} mate scores {mates:>3}   wrong PV {wrong:>3}"
          + (f"   ({100.0*wrong/mates:.1f}%)" if mates else "   (vacuous)"))
    for fen, v, d, why in rows[:6]:
        print(f"    WRONG mate {v:>4} depth {d:>2} {fen[:42]}  {why}")
