#!/usr/bin/env python3
"""job68f : is the mate-forfeit GENERAL, or one board? (the one-fixture rule applied to my own sharpest case)

F171 showed the base reporting cp 0 and playing a move that forfeits a mate in one. One board. This searches for more
validated threefold roots where the mover has a mate available and checks whether the base's chosen move keeps or loses it.
"""
import re, subprocess, os, sys, itertools
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job59"))
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")


def conn(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def mates_in_1(b):
    return [m.uci() for m in b.legal_moves if (lambda c: (c.push(m), c.is_checkmate())[1])(b.copy())]


def find_neutral_cycle(fen):
    b = chess.Board(fen)
    target = (b.board_fen(), b.turn, b.castling_xfen())
    cf = b.castling_xfen() or '-'
    found = []

    def dfs(bb, path):
        if found:
            return
        if len(path) == 4:
            if (bb.board_fen(), bb.turn, bb.castling_xfen()) == target:
                found.append(list(path))
            return
        for m in bb.legal_moves:
            if bb.is_capture(m):
                continue
            bb.push(m)
            if (bb.castling_xfen() or '-') != cf or bb.is_check():
                bb.pop()
                continue
            bb.pop()
            bb.push(m)
            dfs(bb, path + [m.uci()])
            bb.pop()
    dfs(b, [])
    return found[0] if found else None


# candidate positions where the side to move has mate in 1 and quiet king/rook shuttles exist
CANDS = [
    "6k1/5ppp/8/8/8/8/5PPP/1Q4K1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/1R4K1 w - - 0 1",
    "5k2/5ppp/8/8/8/8/5PPP/1Q4K1 w - - 0 1",
    "6k1/6pp/8/8/8/8/6PP/1Q4K1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/Q5K1 w - - 0 1",
    "1k6/1p6/8/8/8/8/1P6/1Q4K1 w - - 0 1",
    "8/8/8/8/8/5k2/8/5K1Q w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/2Q3K1 w - - 0 1",
]
pb = conn(BASE)
pp = conn(PC)
print("| board | cycle | 3-fold? | mover mate-in-1 at root | base move | base forfeits? | PC move | PC forfeits? |")
print("|---|---|---|---|---|---|---|---|")
kept = tested = 0
for fen in CANDS:
    cyc = find_neutral_cycle(fen)
    if not cyc:
        print("| `%s` | none | - | - | - | - | - | - |" % fen)
        continue
    moves = cyc * 2
    ok, msg = check_fixture(fen, moves, expect=3)
    if not ok:
        print("| `%s` | %s | **REJECTED** | - | - | - | - | - |" % (fen, " ".join(cyc)))
        continue
    b = chess.Board(fen)
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    m1 = mates_in_1(b)
    if not m1:
        print("| `%s` | %s | yes | none | - | - | - | - |" % (fen, " ".join(cyc)))
        continue
    tested += 1
    lb, bmb = go(pb, fen, moves, 10)
    lp, bmp = go(pp, fen, moves, 10)
    def forfeits(bm):
        c = b.copy()
        mm = chess.Move.from_uci(bm)
        if mm not in c.legal_moves:
            return "illegal"
        c.push(mm)
        # the OPPONENT moves next; is the mate gone means: white no longer has mate in 1 after black replies?
        # simpler: did the move itself mate? if not, did it give up a mate that was available?
        return "no" if bm in m1 else "yes"
    fb, fp = forfeits(bmb), forfeits(bmp)
    kept += (fb == "yes")
    print("| `%s` | %s | yes | %s | %s | %s | %s | %s |" % (
        fen, " ".join(cyc), ",".join(m1), bmb, "**YES**" if fb == "yes" else fb, bmp, "**YES**" if fp == "yes" else fp))
pb.stdin.write("quit\n"); pb.stdin.flush()
pp.stdin.write("quit\n"); pp.stdin.flush()
print()
print("boards with a mate in 1 at the threefold root: %d | base forfeited it on %d" % (tested, kept))
