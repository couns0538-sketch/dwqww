#!/usr/bin/env python3
"""job63 : does the PC's drawn-root repair stay adequate on 23-F60's SECOND board?

Same method as job62/23-F129, including the CORRECTED static-exchange routine (comparing capture SQUARES, which is what
my first attempt failed to do).
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
PC = os.path.expanduser("~/pcbuild/forge")
FEN = "5k2/1p4p1/2p2p1p/p2p4/P2PqP2/1QP3P1/1P3P2/5K2 b - - 16 35"
VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


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


def go(p, fen, moves, depth):
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


def best_exchange_for_side_to_move(b):
    """Best net material the side to move can win by capturing, by static exchange on the capture SQUARE."""
    best = 0
    for m in b.legal_moves:
        if not b.is_capture(m):
            continue
        victim = b.piece_at(m.to_square)
        if victim is None:
            continue
        gain = VAL.get(victim.piece_type, 0)
        c = b.copy(); c.push(m)
        # recaptures must target the SAME square
        recaps = [r for r in c.legal_moves if r.to_square == m.to_square and c.is_capture(r)]
        if recaps:
            attacker = b.piece_at(m.from_square)
            net = gain - VAL.get(attacker.piece_type, 0)
        else:
            net = gain
        best = max(best, net)
    return best


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


print("board:", FEN)
print("castling field:", chess.Board(FEN).castling_xfen() or '-', "(empty, so any cycle is castling-neutral)")
cyc = find_cycle(FEN)
print("castling-neutral cycle:", cyc)
if not cyc:
    print("P1 KILLED: no castling-neutral cycle -> not constructible")
    sys.exit(2)
moves = cyc * 2 + [] if False else cyc * 2
ok, msg = check_fixture(FEN, moves, expect=3)
print("validator:", "PASS" if ok else "**REJECTED**", "|", msg)
if not ok:
    sys.exit(3)

root = chess.Board(FEN)
for mv in moves:
    root.push(chess.Move.from_uci(mv))

print()
print("| build | move | score | nodes | material the OPPONENT can win after it |")
print("|---|---|---|---|---|")
res = {}
for name, exe, depth in (("base", BASE, 10), ("PC r15", PC, 12)):
    p = conn(exe)
    (k, v, n), bm = go(p, FEN, moves, depth)
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    b = root.copy()
    m = chess.Move.from_uci(bm)
    legal = m in b.legal_moves
    if legal:
        b.push(m)
        loss = best_exchange_for_side_to_move(b)   # opponent to move now, so this is what THEY win
    else:
        loss = None
    res[name] = (bm, k, v, n, legal, loss)
    print("| %s | %s | %s %d | %d | %s |" % (name, bm, k, v, n,
                                             ("%+d" % loss) if loss is not None else "ILLEGAL MOVE"))
print()
b_, p_ = res["base"], res["PC r15"]
print("P2 base returns 0 nodes:", b_[3] == 0, "(nodes %d)" % b_[3])
print("P3 PC's move loses less material than base's:", (p_[5] is not None and b_[5] is not None and p_[5] < b_[5]),
      "| base loss %+d, PC loss %+d" % (b_[5], p_[5]))
print("P4 absolute loss smaller than F129's +6:", b_[5] < 6, "| base loss %+d" % b_[5])
