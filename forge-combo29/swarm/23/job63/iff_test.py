#!/usr/bin/env python3
"""job63c : EARN THE "IFF" in 23-F125. The "if" half (3+ occurrences bail) is tested on 5 counts on one board; the
"ONLY IF" half (2 occurrences NEVER bail) rested on that same board. Test it on several boards of different character.
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
    ("bare kings", "8/8/8/8/8/8/8/K6k w - - 0 1"),
    ("K+Q v K", "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
    ("pawns only", "7k/6pp/8/8/8/8/6PP/7K w - - 0 1"),
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
            # MY FIRST VERSION FORBADE KING AND ROOK MOVES, which on a K+R v K board is every legal move — so all five
            # boards were "excluded" and the test covered nothing. What matters is not the piece type but whether the
            # CYCLE leaves the castling field unchanged (23-F122's sharpening). Check the field, not the mover.
            b.push(m)
            if (b.castling_xfen() or '-') != start_cast:
                b.pop()
                continue
            b.pop()
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


p = conn()
print("| board | cycle | occ 2 -> nodes | occ 3 -> nodes | 'only if' holds? |")
print("|---|---|---|---|---|")
holds = 0
tot = 0
for label, fen in BOARDS:
    cyc = find_cycle(fen)
    if not cyc:
        print("| %s | **no castling-neutral cycle** | - | - | EXCLUDED |" % label)
        continue
    two = cyc
    three = cyc * 2
    ok2, m2 = check_fixture(fen, two, expect=2)
    ok3, m3 = check_fixture(fen, three, expect=3)
    if not (ok2 and ok3):
        print("| %s | %s | **validation failed** | - | EXCLUDED |" % (label, " ".join(cyc)))
        continue
    (k2, v2, n2), _ = go(p, fen, two, 10)
    (k3, v3, n3), _ = go(p, fen, three, 10)
    good = (n2 > 0) and (n3 == 0)
    holds += good
    tot += 1
    print("| %s | %s | %d | %d | %s |" % (label, " ".join(cyc), n2, n3, "yes" if good else "**NO**"))
p.stdin.write("quit\n"); p.stdin.flush()
print()
print("'ONLY IF' (2 occurrences never bail) held on %d of %d boards" % (holds, tot))
print("=> the iff in 23-F125 is earned on %d boards" % tot if holds == tot else "=> iff NOT earned; F125 must be split")
