#!/usr/bin/env python3
"""job64 : does the bail fire when the threefold is in the HISTORY but not at the ROOT?

S-A threefold root (known bail) | S-B threefold in history, one ply on | S-C control with only two occurrences.
"""
import re, subprocess, os, sys
sys.path.insert(0, '../job59')
import chess
from validate import check_fixture, count_occurrences, identity

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE = os.path.expanduser("~/build/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
CYC = "b8c8 a1b2 c8b8 b2a1".split()


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


def final_identity(fen, moves):
    b = chess.Board(fen)
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    return identity(b), b


threefold = CYC * 2                      # root at plies 0, 4, 8
advanced = threefold + ["d5d6"]           # one ply on: nothing repeated at the searched position
two_occ = CYC * 1 + ["d5d6"]              # control: the earlier position occurred only twice

print("== fixture checks ==")
ok, msg = check_fixture(FEN, threefold, expect=3)
print("  threefold root      :", "PASS" if ok else "REJECTED", "|", msg)
print("  threefold+1 ply     : root occurrences =", count_occurrences(FEN, advanced))
print("  two-occ +1 ply      : root occurrences =", count_occurrences(FEN, two_occ))
print()
print("| case | moves | root occ | nodes | score | bestmove | verdict |")
print("|---|---|---|---|---|---|---|")
p = conn()
for label, moves in (("S-A threefold root", threefold),
                     ("S-B threefold + 1 ply", advanced),
                     ("S-C control two occ + 1 ply", two_occ)):
    occ = count_occurrences(FEN, moves)
    (k, v, n), bm = go(p, FEN, moves, 10)
    print("| %s | %s | %d | %d | %s %d | %s | %s |" % (
        label, " ".join(moves[-4:]) + ("..." if len(moves) > 4 else ""), occ, n, k, v, bm,
        "**BAIL**" if n == 0 else "searched"))
p.stdin.write("quit\n"); p.stdin.flush()
