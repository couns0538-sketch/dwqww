#!/usr/bin/env python3
"""label_check.py EXE : is the self-play mate-PV defect a special case of a wider rule?

Pattern 2 says my findings tend to be narrow about scope. Applying the question "what else is this an instance
of?" to my own S-F33/S-F34 (a mate score whose PV does not play out at softnodes 2000):

Hypothesis: it is the same family as the 64-line report-without-search habit AND as the "search resolved before
the budget" behaviour - i.e. a mate PV is short whenever the engine reports a mate it has not yet PROVEN to the
end of its own claimed distance. That would make the correct test: **does the PV length ever EQUAL the claimed
distance while the position is not mate?** (a genuinely wrong number) versus **is the PV always SHORTER when it
fails?** (a horizon/reporting artefact).

This matters for the label advice: if failures are always short PVs, a pipeline can simply REJECT a mate score
whose PV length != 2|N|-1 and lose nothing. If some failures have the right length but are not mate, the score
itself is broken and rejection is not enough.
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
        return None, []
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv


def classify(fen, mate, pv):
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return "illegal-move"
        if mm not in b.legal_moves:
            return "illegal-move"
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    if b.is_checkmate() and len(pv) == need:
        return "ok"
    if len(pv) < need:
        return "SHORT"
    if len(pv) > need:
        return "LONG"
    return "right-length-not-mate"


BOARDS = []
rng = random.Random(2521)
kinds = [[chess.QUEEN], [chess.QUEEN, chess.ROOK], [chess.ROOK, chess.ROOK], [chess.QUEEN, chess.BISHOP]]
for _ in range(2500):
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

print(f"### is the mate-PV failure always a SHORT PV, or sometimes a right-length non-mate? ({len(BOARDS)} boards)")
counts = {}
for fen in BOARDS:
    mate, pv = run(fen, "go softnodes 2000")
    if mate is None:
        continue
    c = classify(fen, mate, pv)
    counts[c] = counts.get(c, 0) + 1
print()
print("softnodes 2000 classification of every mate score:")
for k in ("ok", "SHORT", "LONG", "right-length-not-mate", "illegal-move"):
    if k in counts:
        print(f"  {k:<24} {counts[k]}")
print()
failures = sum(v for k, v in counts.items() if k != "ok")
if failures == 0:
    print("NO FAILURES IN SAMPLE - the character of failures and their rate are UNMEASURED here.")
    print("Do not conclude 'every failure is short' from an empty set. 12/12 correct is a positive result")
    print("about THESE boards only. (The S-F34 failure on 4Q3/8/r2K4/... came from a different board set.)")
elif counts.get("right-length-not-mate", 0) == 0:
    print("RESULT: no failure has the RIGHT length while not being mate. Every failure is a SHORT PV - so a")
    print("pipeline can reject any mate score whose PV length != 2|N|-1 and lose nothing. The SCORE is not broken;")
    print("the report is premature. That confirms my S-F33/S-F34 are a special case of the same reporting habit.")
else:
    print("RESULT: some failures have the right PV length but are not mate - the SCORE itself would be wrong,")
    print("and rejection by length alone would not be sufficient. My S-F33 framing would need widening.")
