#!/usr/bin/env python3
"""job56 : which factor carries the 0-node bail? A ladder of minimal edits from a known-bailing base.

Every rung: its own 4-ply cycle found by search, root occurrence count ASSERTED == 3 and ENDING at the root, then
`go depth 10`. A rung whose fixture fails the assertion is EXCLUDED and printed as excluded (23-F113's P4).
"""
import re, subprocess, os, sys, itertools
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
BASE_FEN = "1K6/8/8/3R4/8/8/8/k7 w"

RUNGS = [
    ("BASE (known bail)", BASE_FEN),
    ("L2 +black rook h8", "1K6/8/8/3R4/8/8/8/k6r w"),
    ("L3 +black pawn h7", "1K6/8/8/3R4/8/8/7p/k7 w"),
    ("L4 black king to b2", "1K6/8/8/3R4/8/8/1k6/8 w"),
    ("L5 mirrored, black to move", "1k6/8/8/3r4/8/8/8/K7 b"),
    ("L6 knight added", "1K6/8/8/3R4/8/8/8/k5n1 w"),
    ("L7 pawns added both sides", "1K6/8/8/3R4/8/5P2/6p1/k7 w"),
]


def pk(b):
    f = b.fen().split(' ')
    return ' '.join(f[:2] + f[3:4])


def find_cycle(fen, maxlen=4):
    root = chess.Board(fen)
    target = pk(root)
    found = []

    def dfs(b, path):
        if found:
            return
        if len(path) == maxlen:
            if pk(b) == target:
                found.append(list(path))
            return
        for m in b.legal_moves:
            if b.is_capture(m):
                continue
            b.push(m)
            if not b.is_check():
                dfs(b, path + [m.uci()])
            b.pop()
            if found:
                return

    dfs(root, [])
    return found[0] if found else None


def conn():
    p = subprocess.Popen([BASE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    o = set()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died")
        s = l.strip()
        if s.startswith("option name "):
            o.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in o:
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
            raise RuntimeError("died in search")
        s = l.strip()
        m = INFO.match(s)
        if m:
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            return last, s.split()[1]


print("| rung | fen | cycle | root occ | nodes | score | verdict |")
print("|---|---|---|---|---|---|---|")
p = conn()
rows = []
for label, fen0 in RUNGS:
    b0 = chess.Board(fen0)
    if not b0.is_valid():
        print("| %s | `%s` | - | - | - | - | **INVALID FEN, EXCLUDED** |" % (label, fen0))
        continue
    fen = ' '.join(b0.fen().split(' ')[:4]) + " 0 1"
    cyc = find_cycle(fen)
    if not cyc:
        print("| %s | `%s` | **no cycle** | - | - | - | EXCLUDED (no repeated position reachable) |" % (label, fen0))
        continue
    moves = cyc * 2
    # assert root occurs 3 times and we end at the root
    bb = chess.Board(fen)
    c = {pk(bb): 1}
    for mv in moves:
        m = chess.Move.from_uci(mv)
        if m not in bb.legal_moves:
            c = None
            break
        bb.push(m)
        k = pk(bb)
        c[k] = c.get(k, 0) + 1
    if c is None or c.get(pk(chess.Board(fen)), 0) != 3 or pk(bb) != pk(chess.Board(fen)):
        print("| %s | `%s` | %s | **assert failed** | - | - | EXCLUDED |" % (label, fen0, " ".join(moves)))
        continue
    (kind, val, nodes), bm = go(p, fen, moves, 10)
    verdict = "**BAIL (0 nodes)**" if nodes == 0 else "searched"
    rows.append((label, nodes))
    print("| %s | `%s` | %s | 3 | %d | %s %d | %s |" % (label, fen0, " ".join(cyc), nodes, kind, val, verdict))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except Exception:
    p.kill()

print()
bailed = [r[0] for r in rows if r[1] == 0]
searched = [r[0] for r in rows if r[1] > 0]
print("rungs that BAILED:", bailed)
print("rungs that SEARCHED:", searched)
if rows:
    base = next((r for r in rows if r[0].startswith("BASE")), None)
    print("P3 control (BASE bails):", bool(base and base[1] == 0), "->", base[1] if base else "not run")
