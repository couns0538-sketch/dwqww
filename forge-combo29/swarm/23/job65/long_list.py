#!/usr/bin/env python3
"""job65 : does the three-occurrence threshold hold when the repeated position is at the END of a LONG move list?

Builds a 12-ply preamble, then repeats an END position n times, so the searched position is NOT the game's starting
position. Every fixture validated by job59/validate.py on the SEARCHED position's own count.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import identity

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
START = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"


def ident(b):
    return identity(b)


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
        if s.startswith("option name"):
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


def build(preamble_len, n):
    """Reach a position via a preamble, then repeat a 4-ply cycle to make the END position occur n times."""
    # find the position after a short quiet preamble, then cycle from there
    # MY FIRST PREAMBLE MOVED THE ROOK, which destroys castling on this board (field already '-', but the rook squares
    # matter to legality) and left no castling-neutral cycle — all four cases came back NOT CONSTRUCTIBLE. Build the
    # preamble from the SAME cycle used for the repetitions, so the position stays reachable and the searched position
    # is simply a deeper point on the same shuttle.
    b = chess.Board(START)
    pre = []
    base_cycle = ["b8c8", "a1b2", "c8b8", "b2a1"]
    for i in range(preamble_len):
        mv = base_cycle[i % 4]
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            return None, None
        b.push(m); pre.append(mv)
    if len(pre) < preamble_len:
        return None, None
    # find a 4-ply cycle returning to the CURRENT position
    target = ident(b)
    found = []

    def dfs(bb, path):
        if found:
            return
        if len(path) == 4:
            if ident(bb) == target:
                found.append(list(path))
            return
        for m in bb.legal_moves:
            if bb.is_capture(m):
                continue
            bb.push(m)
            if not bb.is_check():
                dfs(bb, path + [m.uci()])
            bb.pop()
            if found:
                return

    dfs(b, [])
    if not found:
        return None, None
    cyc = found[0]
    moves = pre + cyc * (n - 1)
    return moves, cyc


p = conn()
print("| case | preamble | cycle | searched-pos occ | searched==start? | nodes | verdict |")
print("|---|---|---|---|---|---|---|")
for n in (2, 3, 4, 5):
    moves, cyc = build(12, n)
    if not moves:
        print("| n=%d | **NOT CONSTRUCTIBLE** | - | - | - | - | EXCLUDED |" % n)
        continue
    b = chess.Board(START)
    ids = [ident(b)]
    for mv in moves:
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            ids = None
            break
        b.push(m); ids.append(ident(b))
    if ids is None:
        print("| n=%d | **illegal line** | - | - | - | - | EXCLUDED |" % n)
        continue
    occ = ids.count(ids[-1])
    same_as_start = ids[-1] == ids[0]
    (k, v, nodes), bm = go(p, START, moves, 10)
    ok_expected = (occ == n)
    print("| n=%d | 12 plies | %s | %d %s | %s | %d | %s |" % (
        n, " ".join(cyc), occ, "" if ok_expected else "**(expected %d)**" % n,
        same_as_start, nodes, "**BAIL**" if nodes == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
