#!/usr/bin/env python3
"""opening_pairs.py EXE : measure the both-colours-from-one-opening case (the factor I said was unmeasured).

S-C36 confirmed games are deterministic and claimed, in principle, that N games from N openings with both colours
are not 2N independent samples - but I did NOT measure how the two colour games relate. This measures it:

For a set of openings, play the same start twice: once as given, once with colours REVERSED (using python-chess
mirror). Compare the two move lists. If they are mirrors of each other, the pair carries ONE piece of information,
and the effective sample size really is the number of openings. If they DIFFER, the pair does carry two outcomes,
just not independent ones.

This turns "the factor is unmeasured" into a measurement or a stated impossibility.
"""
import hashlib
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
OPENINGS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
    "rnbqkb1r/pppppppp/5n2/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 1 2",
    "rnbqkbnr/pp2pppp/2p5/3p4/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 3",
]
PLIES = 10


def one_move(fen):
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
    p.stdin.write("go nodes 20000\n"); p.stdin.flush()
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return best


def play(start):
    b = chess.Board(start)
    moves = []
    for _ in range(PLIES):
        if b.is_game_over(claim_draw=True):
            break
        mv = one_move(b.fen())
        if not mv or mv == "0000":
            break
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            break
        if m not in b.legal_moves:
            break
        b.push(m)
        moves.append(mv)
    return moves


print("### both colours from one opening: are the two games related? (S-C36's unmeasured half)")
print(f"{'opening':<34} {'as-given sha':>14} {'mirrored sha':>14}  same?  mirror-of?")
diff_pairs = 0
for start in OPENINGS:
    g = play(start)
    m_start = chess.Board(start).mirror().fen()
    gm = play(m_start)
    hg = hashlib.sha256(" ".join(g).encode()).hexdigest()[:12]
    hm = hashlib.sha256(" ".join(gm).encode()).hexdigest()[:12]
    # a "mirror-of" relationship: the mirrored game's moves equal the square-mirrored moves of the original
    mirrored_moves = []
    for mv in g:
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            break
        mirrored_moves.append(chess.Move(chess.square_mirror(m.from_square),
                                         chess.square_mirror(m.to_square), m.promotion).uci())
    is_mirror = (mirrored_moves == gm)
    if hg != hm:
        diff_pairs += 1
    print(f"{start[:34]:<34} {hg:>14} {hm:>14}  {str(hg==hm):>5}  {is_mirror}")

print()
print(f"openings where the two colour games are DIFFERENT move lists: {diff_pairs}/{len(OPENINGS)}")
print("If they differ, each pair carries two distinct outcomes (though not independent ones); if they are exact")
print("mirrors, the pair carries one. Either way the point stands that repeating an opening adds no information.")
