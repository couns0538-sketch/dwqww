#!/usr/bin/env python3
"""job52 : prospective test - can I name the 0-node drawn-root move IN ADVANCE from 23-F103's rule?

The predictor is implemented independently in python-chess: it never asks the engine for the move.
  class order: pawn-single, pawn-double, pawn-capture, knight, bishop, rook, queen, king
  predicted SET = all members of the first class present.
Then the engine is asked. Its move must be inside the set.

P5 corrected from the prediction file (it had no black king and was illegal); the correction was recorded in
fixture_check.out BEFORE any engine call.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")

CASES = [
    ("P1 pawns both sides, W", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 120 1"),
    ("P2 pawns both sides, B", "r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 120 1"),
    ("P3 white has NO pawns", "8/8/8/8/8/5k2/6pp/7K w - - 120 1"),
    ("P4 black has NO pawns", "7k/8/8/8/8/8/6PP/7K b - - 120 1"),
    ("P5 W pawns + rook", "6k1/8/8/8/8/8/5PPP/R5K1 w - - 120 1"),
    ("C1 CONTROL not drawn", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
]


def klass(b, m):
    pc = b.piece_at(m.from_square)
    if pc.piece_type == chess.PAWN:
        if b.is_capture(m):
            return 2
        if abs(m.to_square - m.from_square) == 16:
            return 1
        return 0
    return {chess.KNIGHT: 3, chess.BISHOP: 4, chess.ROOK: 5, chess.QUEEN: 6, chess.KING: 7}[pc.piece_type]


def predict(fen):
    b = chess.Board(fen)
    legal = list(b.legal_moves)
    if not legal:
        return [], -1
    classes = {}
    for m in legal:
        classes.setdefault(klass(b, m), []).append(m.uci())
    first = min(classes)
    return sorted(classes[first]), first


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    opts = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def go(p, fen, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


print("| case | predicted class | predicted set | size | engine nodes | engine move | inside set? |")
print("|---|---|---|---|---|---|---|")
p = conn()
inside = singletons = drawn = 0
out = []
for label, fen in CASES:
    ps, cls = predict(fen)
    (kind, val, nodes), bm = go(p, fen, 10)
    isin = bm in ps
    out.append((label, ps, nodes, bm, isin))
    if nodes == 0:
        drawn += 1
    if len(ps) == 1:
        singletons += 1
    if isin:
        inside += 1
    print("| %s | %d | %s | %d | %d | %s | %s |" % (
        label, cls, ",".join(ps[:6]) + ("…" if len(ps) > 6 else ""), len(ps), nodes, bm,
        "yes" if isin else "**NO**"))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
print("fixtures that returned 0 nodes (drawn-root path):", drawn, "of", len(CASES) - 1, "drawn fixtures")
print("predicted sets of size 1:", singletons, "of", len(CASES))
print("engine move inside the predicted set:", inside, "of", len(CASES))
print()
print("P4 control check: C1 is NOT drawn (halfmove 0) — its engine move vs prediction is the last row above.")
