#!/usr/bin/env python3
"""job53 : does the index-0 predictor name the move on NATURALLY reached threefold roots?

Stage 1: three self-play games (PC vs itself, go depth 8) from three opening moves.
Stage 2: replay in python-chess, find every position occurring >= 3 times (naturally reached drawn roots).
Stage 3: PREDICT each root's 0-node move with the independent class predictor (no engine output used).
Stage 4: only then ask the base `go depth 10` and compare.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
PC = os.path.expanduser("~/pcbuild/forge")
BASE = os.path.expanduser("~/build/forge")
OPENINGS = ["e2e4", "d2d4", "g1f3"]
MAXPLY = 120


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def bestmove(p, fen, depth=8):
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


def pkey(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


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
        return None, -1
    classes = {}
    for m in legal:
        classes.setdefault(klass(b, m), []).append(m)
    first = min(classes)
    # within class: LOWEST FROM-SQUARE among generated moves (23-F106), then lowest to-square as a tiebreak
    best = min(classes[first], key=lambda m: (m.from_square, m.to_square))
    return best.uci(), first


print("== stage 1: self-play games ==")
p = conn(PC)
roots = []
for op in OPENINGS:
    b = chess.Board()
    b.push(chess.Move.from_uci(op))
    counts = {}
    counts[pkey(b)] = 1
    hist = []
    for ply in range(MAXPLY):
        if b.is_game_over(claim_draw=True):
            break
        (kind, val, nodes), bm = bestmove(p, b.fen(), 8)
        try:
            m = chess.Move.from_uci(bm)
        except Exception:
            break
        if m not in b.legal_moves:
            print("  opening %s: engine returned ILLEGAL %s - game stopped" % (op, bm))
            break
        b.push(m)
        hist.append(bm)
        k = pkey(b)
        counts[k] = counts.get(k, 0) + 1
        if counts[k] == 3:
            roots.append((op, ply + 2, b.fen()))
            break
    print("  opening %-5s plies %3d | final %s | threefold reached: %s" % (
        op, len(hist), "drawn" if b.is_game_over(claim_draw=True) else "not drawn",
        "YES" if counts.get(pkey(b), 0) >= 3 else "no"))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
print("== stage 3: PREDICT each natural root (no engine output used here) ==")
print("== stage 4: THEN ask the base ==")
print()
print("| root | fen | class | predicted | engine nodes | engine move | class ok? | exact? |")
print("|---|---|---|---|---|---|---|---|")
q = conn(BASE)
n_roots = n_class = n_exact = n_zero = n_pawn = 0
for op, ply, fen in roots:
    pred, cls = predict(fen)
    (kind, val, nodes), bm = bestmove(q, fen, 10)
    b = chess.Board(fen)
    same_class = (bm in [m.uci() for m in b.legal_moves if klass(b, m) == cls])
    exact = (bm == pred)
    n_roots += 1
    n_class += same_class
    n_exact += exact
    n_zero += (nodes == 0)
    n_pawn += (cls == 0)
    print("| %s ply %d | %s | %d | %s | %d | %s | %s | %s |" % (
        op, ply, fen, cls, pred, nodes, bm,
        "yes" if same_class else "**NO**", "**yes**" if exact else "no"))
q.stdin.write("quit\n"); q.stdin.flush()
try:
    q.wait(timeout=10)
except Exception:
    q.kill()

print()
if n_roots == 0:
    print("P1 KILLED: no naturally reached threefold root in these three games - the job has no subject.")
else:
    print("natural roots found: %d" % n_roots)
    print("P2 base returned 0 nodes on: %d of %d" % (n_zero, n_roots))
    print("P3a engine move in the predicted CLASS: %d of %d" % (n_class, n_roots))
    print("P3b engine move EXACTLY the predicted move: %d of %d" % (n_exact, n_roots))
    print("P4 roots whose predicted class is pawn-single: %d of %d" % (n_pawn, n_roots))
