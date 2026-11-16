#!/usr/bin/env python3
"""check_28F4.py EXE LABEL : independent check of seat 28's S-F4.

Claim (seat 28, base tree): the 0-node root adjudication also fires on `board.is_repetition()`. A mate-in-one
board reached a THIRD time by legal moves answers `f2f3`/`cp 0`/0 nodes, where the identical board given by
`position fen` answers `a1a8`/`mate 1`/126 nodes. So a patch removing only the halfmove term leaves this door open.

My check, written from the claim (not their script):
  1. find a position with mate in 1 available;
  2. reach the SAME board a third time by a real move list (a shuffle cycle, repeated);
  3. send it two ways: as `position fen` and as `position startpos moves ...`;
  4. compare score, nodes, and bestmove;
  5. assert the FEN path gives mate 1, and report whether the move-list path gives cp 0.
Also run it on BOTH builds (base and PC r15 under PC20) so the answer names the build.
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
LABEL = sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "PC20"
EXTRA = PC20 if MODE == "PC20" else []


def run(position_cmd, depth=6):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{position_cmd}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


# Build the test position: start from startpos, play a 4-ply knight shuffle cycle TWICE, which returns to the
# start position a third time. Then check whether that repeated board (startpos) has a mate in 1 -- it does not,
# so we instead use a board that DOES have mate in 1 and reach IT three times.
# Simplest reliable construction: a position with mate in 1, then a 4-ply reversible cycle played twice.
MATE_IN_1 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"   # Ra8#
b = chess.Board(MATE_IN_1)
m1 = [mv.uci() for mv in b.legal_moves if b.gives_check(mv)]
mated = False
for mv in b.legal_moves:
    b.push(mv)
    if b.is_checkmate():
        mated = True
        best_mate = mv.uci()
        b.pop()
        break
    b.pop()
print(f"### {LABEL} ({MODE}, Threads 1, Hash 16)")
print(f"test position: {MATE_IN_1}")
print(f"  python-chess: a mating move exists = {mated} ({best_mate if mated else '-'})")

sc_fen, bm_fen, nd_fen = run(f"position fen {MATE_IN_1}", depth=5)
print(f"  as `position fen`                -> score {sc_fen}, bestmove {bm_fen}, nodes {nd_fen}")

# Now reach the same board three times by a move list. Start from that board and play a reversible cycle 2x.
start = chess.Board(MATE_IN_1)
# find a reversible cycle: white and black each move out and back
cycle = None
for wm in start.legal_moves:
    start.push(wm)
    wr = [x for x in start.legal_moves
          if x.from_square == wm.to_square and x.to_square == wm.from_square]
    for wb in wr:
        start.push(wb)
        for bm2 in start.legal_moves:
            start.push(bm2)
            br = [x for x in start.legal_moves
                  if x.from_square == bm2.to_square and x.to_square == bm2.from_square]
            for bb in br:
                start.push(bb)
                ok = start.board_fen() == chess.Board(MATE_IN_1).board_fen()
                start.pop()
                if ok:
                    cycle = (wm, wb, bm2, bb)
                    break
            start.pop()
            if cycle:
                break
        start.pop()
        if cycle:
            break
    start.pop()
    if cycle:
        break

if not cycle:
    print("  could not construct a reversible cycle on this board; claim NOT tested")
    sys.exit(2)

mvlist = []
for _ in range(2):
    for mv in cycle:
        mvlist.append(mv.uci())
print(f"  repeated cycle (2x) move list: {' '.join(mvlist)}")

# replay from the test position and confirm a threefold, and that the board equals the FEN board
b2 = chess.Board(MATE_IN_1)
for u in mvlist:
    b2.push(chess.Move.from_uci(u))
print(f"  reached clock {b2.halfmove_clock}, is_repetition(3)={b2.is_repetition(3)}, "
      f"same board as FEN = {b2.board_fen() == chess.Board(MATE_IN_1).board_fen()}")

sc_rep, bm_rep, nd_rep = run(f"position fen {MATE_IN_1} moves {' '.join(mvlist)}", depth=5)
print(f"  as `position fen ... moves ...`  -> score {sc_rep}, bestmove {bm_rep}, nodes {nd_rep}")

print()
if sc_fen == ("mate", 1) and sc_rep == ("cp", 0):
    print("CONFIRMS seat 28 S-F4: the same board answers mate 1 via `position fen` and cp 0 with 0 nodes")
    print("after being reached a third time by a move list, so the repetition adjudication also skips the search.")
    sys.exit(0)
elif sc_rep == sc_fen:
    print("DOES NOT REPRODUCE: the move-list path gives the same answer as the FEN path.")
    sys.exit(1)
else:
    print(f"DIFFERENT BUT NOT THE CLAIMED PATTERN: fen {sc_fen} vs move-list {sc_rep}")
    sys.exit(3)
