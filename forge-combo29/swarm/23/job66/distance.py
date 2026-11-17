#!/usr/bin/env python3
"""job66 : the DISTANCE axis on a busy board — does the SPACING of the three occurrences matter?"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import identity

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
BOARD = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w - - 0 1"  # dense middlegame, no castling rights


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


def go(p, moves, depth=10):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (BOARD, " ".join(moves))); p.stdin.flush()
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


def find_cycle_from(fen, castfield):
    b = chess.Board(fen)
    target = identity(b)
    found = []

    def dfs(bb, path):
        if found:
            return
        if len(path) == 4:
            if identity(bb) == target:
                found.append(list(path))
            return
        for m in bb.legal_moves:
            if bb.is_capture(m):
                continue
            bb.push(m)
            if (bb.castling_xfen() or '-') != castfield or bb.is_check():
                bb.pop()
                continue
            bb.pop()
            bb.push(m)
            dfs(bb, path + [m.uci()])
            bb.pop()
            if found:
                return

    dfs(b, [])
    return found[0] if found else None


castf = chess.Board(BOARD).castling_xfen() or '-'
CYC_A = find_cycle_from(BOARD, castf)
print("board:", BOARD)
print("cycle from the root (castling-neutral):", CYC_A)
if not CYC_A:
    print("P1 KILLED: no castling-neutral cycle from this board -> still unbuildable")
    sys.exit(2)

# a second, DIFFERENT loop from the position after CYC_A, for the filler
mid = chess.Board(BOARD)
for mv in CYC_A:
    mid.push(chess.Move.from_uci(mv))
CYC_B = find_cycle_from(mid.fen(), mid.castling_xfen() or '-')
print("filler loop from the mid position:", CYC_B)

D1 = CYC_A * 2
D2 = (CYC_A + (CYC_B or [])) * 1 + CYC_A if CYC_B else None
D3 = CYC_A + (CYC_B or []) + CYC_A if CYC_B else None

p = conn()
print()
print("| case | spacing | line len | searched-pos occ | castling constant? | nodes | verdict |")
print("|---|---|---|---|---|---|---|")
for label, moves, expect in (("D1 0/4/8", D1, 3), ("D2 0/8/16", D2, 3), ("D3 0/4/12", D3, 3),
                             ("C  two occurrences", CYC_A, 2)):
    if not moves:
        print("| %s | - | - | - | - | - | NOT CONSTRUCTIBLE |" % label)
        continue
    b = chess.Board(BOARD); ids = [identity(b)]; ok = True; fields = [b.castling_xfen() or '-']
    for mv in moves:
        m = chess.Move.from_uci(mv)
        if m not in b.legal_moves:
            ok = False
            break
        b.push(m); ids.append(identity(b)); fields.append(b.castling_xfen() or '-')
    if not ok:
        print("| %s | - | **illegal line** | - | - | - | EXCLUDED |" % label)
        continue
    occ = ids.count(ids[-1])
    const = len(set(fields)) == 1
    (k, v, nodes), bm = go(p, moves, 10)
    print("| %s | %s | %d | %d%s | %s | %d | %s |" % (
        label, " ".join(moves)[:28], len(moves), occ, "" if occ == expect else " **(want %d)**" % expect,
        const, nodes, "**BAIL**" if nodes == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
