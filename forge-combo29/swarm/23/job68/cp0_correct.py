#!/usr/bin/env python3
"""job68e : is the bail's `cp 0` ever WRONG — i.e. a genuine threefold root from which the mover can still mate?

The bail hard-returns cp 0. If a position is drawn by repetition BUT the mover has a forced mate available, then cp 0
understates the truth — the game is drawn only if the DRAW IS CLAIMED, and a winner would not claim. 23-F63 examined this
once through a "mate fits in the slack" rule; this asks it as a plain DTM question on validated threefold roots using the
repaired prover (23-F121).
"""
import re, subprocess, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PROVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job58", "prover.py")


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if l.strip() == "uciok":
            break
    p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + " ".join(moves)) if moves else "")); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


# K+Q v K with a mate in 1 available AND a repetition cycle available. If the cycle is sent twice the root is a genuine
# threefold, and the mover (White) has mate in 1 — so cp 0 is a draw score on a position where the winner would not claim.
BOARDS = [
    ("KQK mate-in-1 + cycle", "6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w - - 0 1", ["g1h1", "g8h8", "h1g1", "h8g8"]),
    ("KRK mate-in-1 + cycle", "6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1", ["g1h1", "g8h8", "h1g1", "h8g8"]),
    ("KQK mate available + cycle", "8/8/8/8/8/5k2/8/5K1Q w - - 0 1", ["f1g1", "f3g3", "g1f1", "g3f3"]),
]
p = conn()
print("| board | validated 3-fold? | base score / nodes | move | mover can mate? | verdict on cp 0 |")
print("|---|---|---|---|---|---|")
for label, fen, cyc in BOARDS:
    moves = cyc * 2
    ok, msg = check_fixture(fen, moves, expect=3)
    if not ok:
        print("| %s | **no valid cycle: %s** | - | - | - | EXCLUDED |" % (label, msg.split('|')[0].strip()))
        continue
    last, bm = go(p, fen, moves, 10)
    # is there a mate in 1 for the mover from the ROOT?
    b = chess.Board(fen)
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    mates = [m.uci() for m in b.legal_moves
             if (lambda c: (c.push(m), c.is_checkmate())[1])(b.copy())]
    print("| %s | yes | %s %d / %d | %s | %s | %s |" % (
        label, last[0], last[1], last[2], bm,
        ("YES " + ",".join(mates)) if mates else "no",
        "**cp 0 is a DRAW score but the mover has mate in 1 — understates**" if mates else "cp 0 correct"))
p.stdin.write("quit\n"); p.stdin.flush()
