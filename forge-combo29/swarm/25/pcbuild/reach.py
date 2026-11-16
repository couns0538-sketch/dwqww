#!/usr/bin/env python3
"""reach.py EXE LABEL : WALK a real game to halfmove clock 99 and ask the engine there.

The point (coordinator's task 1): decide whether a clock-99 position with the game still live is REACHABLE
by a legal move list, and if so write down that exact move list and the engine's answer at each ply.

Note on the rule, because it matters for what is being constructed: a move that captures or moves a pawn
RESETS the halfmove clock to 0. So the clock climbs only on non-resetting moves. A position at clock 99 is
therefore reached by 99+ consecutive non-resetting plies — and it is LIVE (not drawn) iff each side still has
a capture or pawn move available somewhere in the game tree. That is exactly the condition under test: 99
non-resetting plies walked, with resetting moves still on the board.

Construction: from a start position, repeatedly pick a legal NON-resetting move (deterministic RNG, seed
2521), rejecting any move that would make the position occur a third time (so the game cannot end by
repetition) or that ends the game. Stop at clock 99. Then ask the engine: `go depth 10` with PC20/S14 and
record its score, node count and move.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXE = sys.argv[1]
LABEL = sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "PC20"
EXTRA = PC20_EXTRA if MODE == "PC20" else []
TARGET = int(sys.argv[4]) if len(sys.argv) > 4 else 99

import random
rng = random.Random(2521)


def engine(fen, depth=10):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

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
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


STARTS = [
    # both sides have rooks/kings free to wander, pawns blocked so a long quiet walk exists
    ("KRP/rooks", "8/8/4k3/8/8/4K3/4P3/4R2r w - - 0 1"),
    ("rooks+knights", "8/8/3nk3/8/8/3NK3/8/R6r w - - 0 1"),
    ("queens+rooks", "8/8/3qk3/8/8/3QK3/8/R6r w - - 0 1"),
]

walked = False
for name, start in STARTS:
    b = chess.Board(start)
    if not b.is_valid():
        print(f"{name}: start not legal, skipped")
        continue
    counts = {}
    key = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
    counts[key] = 1
    moves = []
    while b.halfmove_clock < TARGET and len(moves) < 400:
        cands = []
        for m in b.legal_moves:
            if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN:
                continue                      # would reset the clock
            if m.promotion:
                continue
            b.push(m)
            if b.is_game_over(claim_draw=False):
                b.pop()
                continue
            k = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
            if counts.get(k, 0) + 1 >= 3:      # would make a threefold
                b.pop()
                continue
            counts[k] = counts.get(k, 1) + 1   # provisional
            counts[k] -= 1
            b.pop()
            cands.append(m)
        if not cands:
            break
        m = rng.choice(cands)
        b.push(m)
        k = (b.board_fen(), b.turn, b.castling_rights, b.ep_square)
        counts[k] = counts.get(k, 0) + 1
        moves.append(m.uci())

    print("=" * 74)
    print(f"start {name}: {start}")
    print(f"  walked {len(moves)} non-resetting plies, halfmove clock now {b.halfmove_clock}")
    print(f"  terminal? checkmate={b.is_checkmate()} stalemate={b.is_stalemate()} "
          f"threefold={b.is_repetition(2)} insufficient={b.is_insufficient_material()}")
    if b.halfmove_clock >= TARGET and not b.is_game_over(claim_draw=False):
        resets = sum(1 for m in b.legal_moves
                     if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN)
        print(f"  RESET moves still available: {resets}  -> the position is LIVE, not drawn")
        print(f"  clock-99 FEN: {b.fen()}")
        print(f"  exact move list ({len(moves)} plies):")
        print("   ", " ".join(moves))
        sc, bm, nd = engine(b.fen())
        print(f"  ENGINE on {LABEL}: score {sc}, nodes {nd}, bestmove {bm}")
        # what it would have said with the clock at 0 on the same board
        b0 = chess.Board(b.fen())
        b0.halfmove_clock = 0
        sc0, bm0, nd0 = engine(b0.fen())
        print(f"  same board at clock 0 : score {sc0}, nodes {nd0}, bestmove {bm0}")
        walked = True
        break

if not walked:
    print("NO WALK FOUND: could not reach clock 99 with a live game from these starts.")
