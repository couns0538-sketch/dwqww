#!/usr/bin/env python3
"""hypothesis_test.py EXE : test the claim that a horizon seeing mate-in-k also sees shorter mates.

THE HYPOTHESIS (from S-C32/S-C31, unproven): a shallow search that reports `mate N` appears to have found the
SHORTEST mate its horizon can see - so "right length + checkmate" essentially implies "correct distance", and the
length filter is near-exact on its ACCEPT side.

THE TEST, stated so it can fail:
  For boards with a known short mate, find the SHALLOWEST depth at which the engine reports a mate at all. At that
  depth, does it already report the TRUE (shallowest) distance, or does the reported distance fall as depth grows?
  If the first mate distance reported is ALWAYS the final one, the hypothesis holds (the search does not report
  longer mates on the way down).
  If the reported distance sometimes DECREASES with depth - mate 5 at depth 8, mate 3 at depth 12 - then a shallow
  search CAN report an over-long mate, and the filter would PASS it: a blind spot.

This is the direct test the hypothesis implies. It does not need PV lengths at all - just whether the reported mate
NUMBER ever falls with depth.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]


def run(fen, depth):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv " in s:
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score mate (-?\d+)", last or "")
    return int(m.group(1)) if m else None


BOARDS = []
rng = random.Random(2521)
kinds = [[chess.QUEEN, chess.ROOK], [chess.QUEEN], [chess.ROOK, chess.ROOK], [chess.QUEEN, chess.BISHOP]]
for _ in range(4000):
    w = list(rng.choice(kinds))
    sqs = rng.sample(range(64), 2 + len(w))
    b = chess.Board(None)
    b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
    for i, pt in enumerate(w):
        b.piece_at(sqs[0])  # no-op keeps the import honest
        b.set_piece_at(sqs[2 + i], chess.Piece(pt, chess.WHITE))
    b.turn = chess.WHITE
    b.clear_stack()
    if b.is_valid() and not b.is_game_over(claim_draw=False) and not b.is_insufficient_material():
        f = b.fen()
        if f not in BOARDS:
            BOARDS.append(f)
    if len(BOARDS) >= 20:
        break

print("### does the reported mate distance FALL with depth? (tests the filter's accept-side hypothesis)")
print(f"{'board':<38} " + " ".join(f"d{d:<2}" for d in (6, 8, 10, 12, 14, 16)) + "  first  final  monotone?")
fell = 0
for fen in BOARDS:
    series = [run(fen, d) for d in (6, 8, 10, 12, 14, 16)]
    mates = [x for x in series if x is not None and x > 0]
    if not mates:
        continue
    first = mates[0]
    final = mates[-1]
    monotone = all(mates[i] >= mates[i + 1] for i in range(len(mates) - 1))
    if final < first:
        fell += 1
    cells = " ".join(f"{str(x):<3}" if x is not None else " - " for x in series)
    print(f"{fen[:38]:<38} {cells}  {first:>5}  {final:>5}  {monotone}")

print()
print(f"boards where the reported mate distance FELL as depth grew: {fell}")
if fell == 0:
    print("HYPOTHESIS SUPPORTED on this sample: the first mate distance reported was also the final one. So a shallow")
    print("search appears to report the SHORTEST mate it can see, which is why a right-length PV has always been")
    print("correct - the accept side is near-exact here.")
else:
    print(f"HYPOTHESIS REFUTED on {fell} boards: a shallow search DID report an over-long mate before converging, which")
    print("is exactly the blind spot the length filter would pass. So the filter's accept side is NOT safe.")
