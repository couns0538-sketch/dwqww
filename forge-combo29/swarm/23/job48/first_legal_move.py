#!/usr/bin/env python3
"""job48 : is the base's 0-node drawn-root move the FIRST LEGAL MOVE, and is it always legal?

For each drawn root: ask the base for `go depth 10`, record nodes + bestmove, and compare against python-chess's legal
move list from the SAME position (established by replaying the validated move list in python-chess, never by trusting
the engine). Also: is the emitted move in the legal set at all, and what is its index in python-chess's iteration order?

IMPORTANT CAVEAT PRINTED WITH THE RESULT: python-chess's legal-move ITERATION ORDER is not the engine's generation
order. So "index 0 in python-chess" is evidence about the move being a plausible first entry, NOT proof about the
engine's generator. P2 is phrased accordingly and the write-up must not upgrade it.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")

CASES = [
    ("D1 threefold W", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
     "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"),
    ("D2 threefold B", "1K6/8/8/3R4/8/8/8/k7 b - - 0 1",
     "a1b1 d5d6 b1a1 d6d5 a1b1 d5d6 b1a1 d6d5"),
    ("D3 threefold c1", "7k/8/8/8/8/8/8/K1R5 w - - 0 1",
     "c1c7 h8g8 c7c1 g8h8 c1c7 h8g8 c7c1 g8h8"),
    ("D4 halfmove150", "1K6/8/8/3R4/8/8/8/k7 w - - 150 1", None),
    ("D5 bare kings", "8/8/8/8/8/8/8/K6k w - - 0 1", None),
    ("C1 CONTROL not drawn", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", None),
]


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
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


def go(p, fen, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s%s\n" % (fen, (" moves " + moves) if moves else "")); p.stdin.flush()
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


def position(fen, moves):
    b = chess.Board(fen)
    if moves:
        for mv in moves.split():
            m = chess.Move.from_uci(mv)
            assert m in b.legal_moves, ("fixture illegal", mv, b.fen())
            b.push(m)
    return b


print("| case | nodes | bestmove | legal? | index in python-chess order | #legal |")
print("|---|---|---|---|---|---|")
rows = []
p = proc(BASE)
for label, fen, moves in CASES:
    b = position(fen, moves)
    legal = [m.uci() for m in b.legal_moves]
    (kind, val, nodes), bm = go(p, fen, moves)
    ok = bm in legal
    idx = legal.index(bm) if ok else -1
    rows.append((label, nodes, bm, ok, idx, len(legal)))
    print("| %s | %d | %s | %s | %s | %d |" % (label, nodes, bm, "yes" if ok else "**NO**",
                                               idx if ok else "-", len(legal)))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
print("== determinism: each drawn root twice, fresh process ==")
for label, fen, moves in CASES[:5]:
    moves_seen = []
    for _ in range(2):
        q = proc(BASE)
        _, bm = go(q, fen, moves)
        q.stdin.write("quit\n"); q.stdin.flush()
        try:
            q.wait(timeout=10)
        except Exception:
            q.kill()
        moves_seen.append(bm)
    print("  %-22s %s %s" % (label, moves_seen, "IDENTICAL" if moves_seen[0] == moves_seen[1] else "**DIFFERS**"))

print()
print("P1 every 0-node move legal:", all(r[3] for r in rows if r[1] == 0))
print("P2 index-0 in python-chess order on how many of the five drawn:", sum(1 for r in rows if r[1] == 0 and r[4] == 0))
print("   indices among drawn roots:", [(r[0], r[4]) for r in rows if r[1] == 0])
print("P4 control searched (nodes > 1000):", rows[-1][1] > 1000, "nodes =", rows[-1][1])
