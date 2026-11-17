#!/usr/bin/env python3
"""job56b : the one variable I skipped in the ladder — CASTLING RIGHTS.

Base board with a legal castling right is not constructible on the sparse endgame (no king/rook placement gives one),
so I build a board that (a) has a cycle, (b) has castling rights, and (c) can be varied to REMOVE the rights while
keeping everything else identical. That contrast is the clean test.
"""
import re, subprocess, os, sys
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")


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


print("== does CASTLING RIGHTS decide it? Same board, rights present vs absent ==")
print()
CASES = [
    ("rights KQkq", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1", "a1b1 a8b8 b1a1 b8a8"),
    ("rights REMOVED (-)", "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1", "a1b1 a8b8 b1a1 b8a8"),
    ("rights KQkq, endgame-like", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 13 7", "a1b1 a8b8 b1a1 b8a8"),
]
p = conn()
print("| case | fen | cycle valid | root occ | nodes | score | verdict |")
print("|---|---|---|---|---|---|---|")
for label, fen, cycstr in CASES:
    b0 = chess.Board(fen)
    cyc = cycstr.split()
    bb = chess.Board(fen)
    c = {pk(bb): 1}
    okc = True
    for mv in cyc * 2:
        m = chess.Move.from_uci(mv)
        if m not in bb.legal_moves:
            okc = False
            break
        bb.push(m)
        k = pk(bb)
        c[k] = c.get(k, 0) + 1
    if not okc:
        print("| %s | `%s` | **illegal cycle** | - | - | - | EXCLUDED |" % (label, fen))
        continue
    rootc = c.get(pk(chess.Board(fen)), 0)
    (kind, val, nodes), bm = go(p, fen, cyc * 2, 10)
    print("| %s | `%s` | yes | %d | %d | %s %d | %s |" % (
        label, fen, rootc, nodes, kind, val, "**BAIL**" if nodes == 0 else "searched"))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
