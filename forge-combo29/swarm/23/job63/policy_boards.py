#!/usr/bin/env python3
"""job63b : does the PC's CLAIM policy hold on more than one claimable-draw board?

23-F128's R3 showed PC cp 425 vs base cp 0 on a claimable threefold -- both defensible. That was one board. This asks
whether the PC is CONSISTENT: if it claims on some claimable roots and not others, "policy difference" is wrong and
"inconsistent" is right.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")

# three claimable threefold roots of different character, all castling-neutral cycles, all with the MOVER WINNING
CASES = [
    ("R3 K+R v K (F128's board)", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1", "b8c8 a1b2 c8b8 b2a1"),
    ("K+Q v K", "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1", None),
    ("pawns+rook (job52 P1)", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", "g1h1 g8h8 h1g1 h8g8"),
]


def find_cycle(fen):
    root = chess.Board(fen)
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
            pc = b.piece_at(m.from_square)
            if pc.piece_type in (chess.KING, chess.ROOK, chess.PAWN):
                continue
            b.push(m)
            if not b.is_check():
                dfs(b, path + [m.uci()])
            b.pop()
            if found:
                return

    dfs(root, [])
    return found[0] if found else None


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def go(p, fen, moves, depth=12):
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


print("| board | base score/nodes | PC score/nodes | PC claims the draw? |")
print("|---|---|---|---|")
res = []
for label, fen, cyc in CASES:
    cyc = cyc.split() if cyc else find_cycle(fen)
    if not cyc:
        print("| %s | - | - | **no castling-neutral cycle** |" % label)
        continue
    moves = cyc * 2
    ok, msg = check_fixture(fen, moves, expect=3)
    if not ok:
        print("| %s | - | - | **REJECTED: %s** |" % (label, msg))
        continue
    out = []
    for exe in (BASE, PC):
        p = conn(exe)
        (k, v, n), bm = go(p, fen, moves, 12)
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
        out.append((k, v, n))
    res.append((label, out[0], out[1]))
    row = [label, out[0], out[1]]
    print("| %s | %s %d / %d | %s %d / %d | %s |" % (
        label, row[1][0], row[1][1], row[1][2], row[2][0], row[2][1], row[2][2],
        "**YES (cp 0)**" if row[2][1] == 0 else "no (reports a win)"))
print()
if res:
    claims = sum(1 for _, b, p in res if p[1] == 0)
    print("PC claimed the draw on %d of %d claimable roots" % (claims, len(res)))
    print("=> consistent policy" if claims in (0, len(res)) else "=> INCONSISTENT: claims on some, not others")
