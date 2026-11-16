#!/usr/bin/env python3
"""cost.py EXE : how much does the clock-99 draw shortcut cost in a WON position, and does it lose it?

Construction: find a position where the engine at clock 0 gives a clearly winning score (>= +500 cp) AND the
clock-resetting moves (captures / pawn pushes) are available so the game can continue at clock 99. Put the same
board at clock 99 and at clock 0 and compare score, move, and nodes.

Then the part that decides "defect" vs "game-losing defect": play the engine's clock-99 move at clock 0 and let
the engine continue from there for a few plies. If the resulting line throws away the win (score falls from
winning to drawn/lost), the shortcut cost the win.
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
DEPTH = 10


def run(fen, depth=DEPTH):
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
    toks = (last or "").split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    return val, best, (int(n.group(1)) if n else 0), pv, (m.group(0) if m else "?")


# Candidate won positions where the winner also has a pawn push / capture available (so a reset exists)
CANDS = [
    # white a queen up, pawns to push
    ("queen up", "r5k1/pp3ppp/8/8/8/8/PP3PPP/R2Q2K1 w - - {c} 1"),
    # white a rook and two pawns up
    ("rook+2P up", "1r4k1/5ppp/8/8/8/8/PP3PPP/R5K1 w - - {c} 1"),
    # white a queen and rook up
    ("Q+R up", "2r3k1/5ppp/8/8/8/8/PP3PPP/R2Q2K1 w - - {c} 1"),
]

print(f"build PC r15 / PC20, Threads 1, Hash 16, depth {DEPTH}")
print()
best_case = None
for name, tpl in CANDS:
    f0 = tpl.format(c=0)
    f99 = tpl.format(c=99)
    b = chess.Board(f0)
    resets = [(m.uci(), b.is_capture(m)) for m in b.legal_moves
              if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN]
    v0, bm0, n0, pv0, s0 = run(f0)
    v99, bm99, n99, pv99, s99 = run(f99)
    print(f"### {name}: {f0}")
    print(f"  clock-resetting moves available: {len(resets)} e.g. {[r[0] for r in resets[:5]]}")
    print(f"  clock 0  : {s0:>12} value {v0} best {bm0} nodes {n0} pv {len(pv0)}")
    print(f"  clock 99 : {s99:>12} value {v99} best {bm99} nodes {n99} pv {len(pv99)}")
    if v0 is not None and v99 is not None and v0 > 400 and v99 == 0:
        print(f"  --> THROWS AWAY {v0} cp of evaluation (winning -> reported draw)")
        if best_case is None:
            best_case = (name, f0, bm0, bm99, v0)
    print()

if best_case is None:
    print("no candidate had a winning clock-0 score that collapses to 0 at clock 99")
    sys.exit(2)

name, f0, bm0, bm99, v0 = best_case
print("=" * 78)
print(f"CONTINUATION TEST on {name}: does the clock-99 move actually forfeit the win?")
b = chess.Board(f0)
try:
    mv = chess.Move.from_uci(bm99)
except ValueError:
    print("bad move from clock 99")
    sys.exit(3)
if mv not in b.legal_moves:
    print(f"clock-99 bestmove {bm99} is not legal here")
    sys.exit(3)
b.push(mv)
print(f"  engine's clock-99 move {bm99} played at clock 0 -> {b.fen()}")
v_after, bm_after, n_after, _, s_after = run(b.fen())
print(f"  engine's own evaluation of the position AFTER that move: {s_after} (value {v_after})")
print(f"  (from the OPPONENT's side, so white's value is {-v_after if v_after is not None else '?'})")
print()
print(f"  clock-0 best move was {bm0} with value {v0}")
print(f"  after the clock-99 move the engine says white is at {-v_after if v_after is not None else '?'}")
lost = v_after is not None and -v_after < v0 / 2
print()
if lost:
    print("VERDICT: the clock-99 move gives up a large part of the win - the shortcut has a real cost.")
else:
    print("VERDICT: the clock-99 move does NOT lose the win on this board; the cost here is the SCORE only.")
