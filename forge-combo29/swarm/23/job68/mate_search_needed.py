#!/usr/bin/env python3
"""job68g : does the base forfeit a mate that requires SEARCH to see (mate in 2+), not just mate in 1?

F172 tested mate in 1, which needs no search. The harder case is a threefold root where the mover has a mate in 2 or 3:
if the base still plays the generator head and gives it up, the mechanism is the same and stronger; if it happens to play
a mating move, then on those boards the unsearched move is harmless and the cost depends on the position.
"""
import re, subprocess, os, sys
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


def forced_mate_plies(fen, limit=6):
    """Smallest N such that the side to move forces mate in N plies, or None. Bounded search."""
    b = chess.Board(fen)

    def can(n, board):
        if n <= 0:
            return False
        for m in board.legal_moves:
            board.push(m)
            try:
                if board.is_checkmate():
                    return True
                replies = list(board.legal_moves)
                if not replies:
                    continue
                if n >= 3 and all(can(n - 2, _push(board, r)) for r in replies):
                    return True
            finally:
                board.pop()
        return False

    def _push(board, r):
        board.push(r)
        return board

    # simpler exact recursion
    def f(board, n):
        if n <= 0:
            return False
        for m in board.legal_moves:
            board.push(m)
            try:
                if board.is_checkmate():
                    return True
                reps = list(board.legal_moves)
                if not reps:
                    continue
                ok = True
                for r in reps:
                    board.push(r)
                    try:
                        sub = f(board, n - 2)
                    finally:
                        board.pop()
                    if not sub:
                        ok = False
                        break
                if ok:
                    return True
            finally:
                board.pop()
        return False

    for n in range(1, limit + 1, 2):
        if f(b, n):
            return n
    return None


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


CANDS = [
    "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/2Q3K1 w - - 0 1",
    "7k/7p/6K1/8/8/8/8/R7 w - - 0 1",
    "6k1/5p1p/6p1/8/8/8/5PPP/1Q4K1 w - - 0 1",
    "8/8/8/8/8/5k2/5p2/5K1Q w - - 0 1",
    "6k1/6pp/8/8/8/8/6PP/R5K1 w - - 0 1",
]
pb = conn(BASE)
pp = conn(PC)
print("| board | cycle | 3-fold | mate in plies | base score/move | base keeps mate? | PC score/move |")
print("|---|---|---|---|---|---|---|")
found = 0
for fen in CANDS:
    cyc = find_neutral_cycle(fen)
    if not cyc:
        print("| `%s` | none | - | - | - | - | - |" % fen)
        continue
    moves = cyc * 2
    ok, msg = check_fixture(fen, moves, expect=3)
    if not ok:
        print("| `%s` | %s | **REJECTED** | - | - | - | - |" % (fen, " ".join(cyc)))
        continue
    b = chess.Board(fen)
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    mp = forced_mate_plies(b.fen(), 5) if False else forced_mate_plies(b.fen(), 5)
    if mp is None or mp <= 1:
        print("| `%s` | %s | yes | %s | - | - | - |" % (fen, " ".join(cyc), mp))
        continue
    found += 1
    lb, bmb = go(pb, fen, moves, 10)
    lp, bmp = go(pp, fen, moves, 10)
    # after the base's move, does the mate still exist for the ORIGINAL mover (now opponent to move)?
    c = b.copy()
    mm = chess.Move.from_uci(bmb)
    keeps = "?"
    if mm in c.legal_moves:
        c.push(mm)
        # now it is the defender's move; the mate for the original mover survives iff every reply allows mate
        keeps = "unknown"
    print("| `%s` | %s | yes | %d plies | %s %d / %s | %s | %s %d / %s |" % (
        fen, " ".join(cyc), mp, lb[0], lb[1], bmb, keeps, lp[0], lp[1], bmp))
pb.stdin.write("quit\n"); pb.stdin.flush()
pp.stdin.write("quit\n"); pp.stdin.flush()
print()
print("boards with a forced mate of 3+ plies at the threefold root: %d" % found)
