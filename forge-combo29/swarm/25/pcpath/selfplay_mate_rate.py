#!/usr/bin/env python3
"""selfplay_mate_rate.py EXE : how often does `go softnodes 2000` emit a mate PV that does not play out?

S-F33 found one case on a single mate-scored position out of 100 middlegame positions. That sample cannot give a
rate. This uses mate-rich endgame boards (where mates DO appear at depth 6-8) and measures:

  M1  of the positions that emit a mate score at softnodes 2000, how many have a PV that is (a) illegal,
      (b) legal but not checkmate, (c) legal and checkmate but the wrong length?
  M2  for those, what does `go nodes 20000` say - does the mate number change (i.e. is the self-play number
      one move pessimistic as in S-F33)?
  M3  the control: the same boards at `go nodes 20000` must be clean.

PVs are sliced from the engine's own line and replayed immediately, never typed.
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
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, [], 0
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    d = re.search(r"depth (\d+)", last)
    return (int(m.group(1)) if m else None), pv, (int(d.group(1)) if d else 0)


def judge(fen, mate, pv):
    b = chess.Board(fen)
    for i, mv in enumerate(pv):
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return "ILLEGAL", f"bad uci {mv}"
        if mm not in b.legal_moves:
            return "ILLEGAL", f"{mv}@{i}"
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    if b.is_checkmate() and len(pv) == need:
        return "OK", f"{len(pv)}/{need}"
    if b.is_checkmate():
        return "WRONG-LEN", f"{len(pv)}/{need}"
    return "NOT-MATE", f"{len(pv)}/{need}"


BOARDS = ["4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1"]
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
    if len(BOARDS) >= 41:
        break

print(f"### self-play mate-PV quality on {len(BOARDS)} mate-rich endgame boards")
print(f"PC r15/PC20, Threads 1, Hash 16; PVs sliced from the engine line and replayed")
print()
sp_mates = {"OK": 0, "NOT-MATE": 0, "ILLEGAL": 0, "WRONG-LEN": 0}
match_mates = {"OK": 0, "NOT-MATE": 0, "ILLEGAL": 0, "WRONG-LEN": 0}
changed = 0
rows = []
for fen in BOARDS:
    m1, pv1, d1 = run(fen, "go softnodes 2000")
    if m1 is None:
        continue
    v1, why1 = judge(fen, m1, pv1)
    sp_mates[v1] += 1
    m2, pv2, d2 = run(fen, "go nodes 20000")
    if m2 is not None:
        v2, why2 = judge(fen, m2, pv2)
        match_mates[v2] += 1
        if m2 != m1:
            changed += 1
    else:
        v2, why2 = "n/a", ""
    if v1 != "OK":
        rows.append((fen, m1, d1, len(pv1), why1, m2, why2))
    print(f"{fen[:44]:<44} sp: mate {m1:>4} depth {d1:>2} {why1:<10} {v1:<10} | match: mate {str(m2):>4} {v2}")

print()
print(f"self-play (softnodes 2000) mate PVs: {sp_mates}")
print(f"match     (nodes 20000)   mate PVs: {match_mates}")
print(f"boards where the self-play mate NUMBER differs from the match number: {changed}")
if rows:
    print()
    print("non-OK self-play rows:")
    for fen, m1, d1, pl, why1, m2, why2 in rows:
        print(f"  {fen} sp mate {m1} ({pl} plies, {why1}) -> match mate {m2} ({why2})")
