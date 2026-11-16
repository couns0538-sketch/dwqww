#!/usr/bin/env python3
"""check_21F2.py EXE : check seat 21's 21-F2.

Claim: after a REFUSED FEN the engine keeps the previous position, still answers readyok, so a GUI syncing on
readyok is handed a move for the WRONG SIDE. With the same board accepted (as `w Q`) it is White's move; with the
FEN refused the answer is Black's move from the old game.

My check, written from the claim, 19-F12-safe (stdin open, read to bestmove before sending anything else):
  case A: a legitimate position (white to move), search it          -> a White move
  case B: send a FEN with an impossible castling right (refused), then `go`
          -> is the answer Black's move from case A?  and did we get readyok anyway?
  case C: the same board with the castling right legal (`w Q`)       -> should be a White move
"""
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
# a middlegame where black is to move after white's reply; used to see whose move comes back
POS_A = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
REFUSED = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1"   # castling right without rook
ACCEPTED = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w Q - 0 1"


def session(plan):
    """plan: list of ('fen', f) or ('go', depth). stdin stays open; read to bestmove each time."""
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    log = []

    def until(word):
        for line in p.stdout:
            log.append(line.rstrip("\n"))
            if line.strip() == word:
                return True
        return False

    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")

    results = []
    for kind, arg in plan:
        if kind == "fen":
            p.stdin.write(f"position fen {arg}\n"); p.stdin.flush()
            p.stdin.write("isready\n"); p.stdin.flush()
            ok = until("readyok")
            results.append(("fen", arg, "readyok" if ok else "NO-READYOK", list(log)))
        else:
            p.stdin.write(f"go depth {arg}\n"); p.stdin.flush()
            best = None
            while True:
                line = p.stdout.readline()
                if not line:
                    break
                s = line.rstrip("\n")
                log.append(s)
                if s.startswith("bestmove"):
                    best = s.split()[-1]
                    break
            results.append(("go", arg, best, list(log)))
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return results


print(f"### check of seat 21's 21-F2 — {EXE} (PC20, Threads 1, Hash 16)")
print()
print("SESSION 1: legit position, then go")
r = session([("fen", POS_A), ("go", 6)])
a_move = r[1][2]
print(f"  A: position accepted; go depth 6 -> bestmove {a_move}")
print(f"     (white to move at {POS_A})")

print()
print("SESSION 2: legit position, go, then a REFUSED fen, then go")
r = session([("fen", POS_A), ("go", 6), ("fen", REFUSED), ("go", 6)])
a1 = r[1][2]
ready = r[2][2]
refused_lines = [l for l in r[2][3] if "invalid" in l.lower() or "Invalid" in l]
b1 = r[3][2]
print(f"  A: go -> {a1}")
print(f"  B: refused FEN answered: {ready}")
print(f"     refusal line(s): {refused_lines[:2]}")
print(f"  C: go after the refusal -> {b1}")

print()
print("SESSION 3: the same board with a LEGAL right (w Q), go")
r3 = session([("fen", ACCEPTED), ("go", 6)])
c1 = r3[1][2]
print(f"  go -> {c1}")

print()
print("VERDICT")
if b1 == a1:
    print(f"  the post-refusal answer EQUALS the earlier white-move answer ({a1}) -> no wrong-side move")
elif b1 == c1:
    print(f"  the post-refusal answer equals the accepted-board answer ({c1}) -> no wrong-side move")
else:
    print(f"  post-refusal answer {b1} differs from both {a1} (earlier, white) and {c1} (accepted board).")
    print("  Seat 21's claim is that it is BLACK'S move from the old game. A black move is identifiable by the")
    print("  piece it moves: on this board black's pieces are on ranks 7-8 in standard squares.")
