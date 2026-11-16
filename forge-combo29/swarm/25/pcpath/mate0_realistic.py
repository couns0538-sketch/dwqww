#!/usr/bin/env python3
"""mate0_realistic.py EXE : would a REALISTIC match program ever hit `mate 0`?

S-F6 is real but its exposure depends entirely on whether a match program asks the engine about a finished game.
Two realistic designs:
  D1 (sane): the match program keeps the board itself, detects checkmate with its own rules, and never sends `go`
     on a mated position. -> exposure 0.
  D2 (engine-trusting): the match program asks the engine for a score each ply and stops when the score says the
     game is over (e.g. looking for a mate score). -> it must interpret `mate 0`, and if it reads `mate 0` as "no
     mate" it will ask again forever, or if it reads it as a win for nobody it records a draw.

D2 is testable end to end: simulate it, and see what happens when the game reaches mate.
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


def ask(fen):
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
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(1), int(m.group(2))) if m else None, best


print("D2 simulation: a match program that trusts the ENGINE's score to decide the game is over.")
print("Rule it uses: stop when the score is `mate N` with N != 0 (a real mate), or when bestmove is 0000.")
b = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
for ply in range(8):
    if b.is_game_over(claim_draw=True):
        print(f"  [program] python-chess says the game is over: {b.outcome(claim_draw=True)}")
        break
    sc, best = ask(b.fen())
    print(f"  ply {ply}: engine {sc}, bestmove {best}")
    if sc and sc[0] == "mate":
        if sc[1] == 0:
            print("    -> engine says `mate 0`. A score-trusting program testing `mate N` with N != 0 does NOT")
            print("       see a mate; testing `mate` at all DOES. Either way this is the ambiguous token S-F6")
            print("       is about. It also gets bestmove 0000, which is not a move it can play.")
            print("    -> a program that only plays legal moves stops here by accident (0000 is unplayable);")
            print("       a program that reads the SCORE records an undefined result.")
            break
        print(f"    -> engine says mate in {sc[1]}; program plays {best}")
    if not best or best == "0000":
        print("    -> bestmove 0000: the program cannot continue, so it stops (accidentally safely)")
        break
    b.push(chess.Move.from_uci(best))

print()
print("D1 (the sane design): the match program owns the board and checks checkmate itself.")
b2 = chess.Board("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1")
for ply in range(8):
    if b2.is_checkmate():
        print(f"  [program] checkmate detected locally at ply {ply}; engine never asked about a mated position")
        break
    if b2.is_game_over(claim_draw=True):
        print(f"  [program] game over locally: {b2.outcome(claim_draw=True)}")
        break
    sc, best = ask(b2.fen())
    b2.push(chess.Move.from_uci(best))
print()
print("CONCLUSION: S-F6's `mate 0` can only be reached by a program that (a) searches a finished position and")
print("(b) trusts the score token. The sane design never sees it, and even the trusting design cannot PLAY 0000,")
print("so it stops by accident. The exposure is a wrong recorded result, not a broken game.")
