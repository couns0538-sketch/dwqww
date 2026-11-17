#!/usr/bin/env python3
"""job63d : EARN the "IF" half (3/4/5 occurrences all bail) on boards other than the original.

23-F132 earned "only if" (2 never bails) on four boards. The "if" half at 4/5/6 occurrences was still one board, so
this runs 3 and 4 occurrences on several boards of different material.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
BOARDS = [
    ("K+R v K", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"),
    ("pawns+rook", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
    ("K+Q v K", "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
    ("pawns only", "7k/6pp/8/8/8/8/6PP/7K w - - 0 1"),
    ("black to move", "1k6/8/8/3r4/8/8/8/K7 b - - 0 1"),
]


def find_cycle(fen):
    root = chess.Board(fen)
    start_cast = root.castling_xfen() or '-'
    rk = (root.board_fen(), root.turn, root.castling_xfen())
    found = []

    def idn(b):
        return (b.board_fen(), b.turn, b.castling_xfen())

    def dfs(b, path):
        if found:
            return
        if len(path) == 4:
            if idn(b) == rk:
                found.append(list(path))
            return
        for m in b.legal_moves:
            if b.is_capture(m):
                continue
            b.push(m)
            if (b.castling_xfen() or '-') != start_cast or b.is_check():
                b.pop()
                continue
            b.pop()
            b.push(m)
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


p = conn()
print("| board | occ 3 | occ 4 | occ 5 | 'if' holds? |")
print("|---|---|---|---|---|")
holds = tot = 0
for label, fen in BOARDS:
    cyc = find_cycle(fen)
    if not cyc:
        print("| %s | **no castling-neutral cycle** | - | - | EXCLUDED (no fixture) |" % label)
        continue
    vals = []
    bad = False
    for n in (3, 4, 5):
        moves = cyc * (n - 1)
        ok, msg = check_fixture(fen, moves, expect=n)
        if not ok:
            vals.append("REJ")
            bad = True
            continue
        (k, v, nodes), _ = go(p, fen, moves, 10)
        vals.append(nodes)
    if bad:
        print("| %s | %s | | | EXCLUDED (validation) |" % (label, " / ".join(str(v) for v in vals)))
        continue
    good = all(x == 0 for x in vals)
    holds += good
    tot += 1
    print("| %s | %d | %d | %d | %s |" % (label, vals[0], vals[1], vals[2], "yes" if good else "**NO**"))
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("'IF' (3, 4, 5 occurrences ALL bail) held on %d of %d boards" % (holds, tot))
