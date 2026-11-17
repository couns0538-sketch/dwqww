#!/usr/bin/env python3
"""job43 : does the short-PV / wrong-distance hazard apply to LOSING mates (mate -N) too?

Ply arithmetic differs by sign: a complete `mate N` (N>0) line is 2N-1 plies; a complete `mate -N` line is 2N plies.
Every PV is replayed in python-chess and the final position must be checkmate.

Usage: python3 losing_mates.py <exe>
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+).*?(?: pv(?: (.+))?)?\s*$")

BOARDS = [("L1 back-rank, 1 legal mv", "7k/8/6K1/8/8/8/8/7Q b - - 0 1"),
          ("L2 corner, 1 legal mv", "k7/8/1K6/8/8/8/8/7Q b - - 0 1")]
DEPTHS = (4, 6, 8, 10, 12)


def proc(exe):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    opts = set()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died during uci")
        s = l.strip()
        if s.startswith("option name "):
            opts.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    if "OwnBook" in opts:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\n")
    p.stdin.write("setoption name Hash value 16\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    return p


def search(p, fen, depth):
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
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
            last = (int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)), (m.group(5) or "").split())
        if s.startswith("bestmove"):
            return last, s.split()[1]


def replay(fen, moves):
    b = chess.Board(fen)
    for mv in moves:
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            return "BAD-TOKEN", None
        if m not in b.legal_moves:
            return "ILLEGAL", None
        b.push(m)
    return ("MATE" if b.is_checkmate() else "NO-MATE"), len(moves)


print("== method control: the replay must accept a mate and reject a truncated one (same helper as job41) ==")
f = chess.Board()
for mv in ("f2f3", "e7e5", "g2g4", "d8h4"):
    f.push(chess.Move.from_uci(mv))
print("fool's mate full ->", "MATE" if f.is_checkmate() else "NOT-MATE")
g = chess.Board()
for mv in ("f2f3", "e7e5", "g2g4"):
    g.push(chess.Move.from_uci(mv))
print("same line minus last move ->", "MATE" if g.is_checkmate() else "NO-MATE (correctly rejected)")
print()

exe = os.path.expanduser(sys.argv[1])
print("build:", exe)
print("| board | depth | score | pv plies | 2N (loss) | replay | bestmove |")
print("|---|---|---|---|---|---|---|")
for label, fen in BOARDS:
    p = proc(exe)
    for d in DEPTHS:
        info, bm = search(p, fen, d)
        if info is None:
            print("| %s | %d | **PARSE FAILURE** | - | - | - | %s |" % (label, d, bm)); continue
        depth, kind, val, nodes, pv = info
        verdict, nply = replay(fen, pv)
        if kind == "mate" and val < 0:
            need = 2 * abs(val)
            print("| %s | %d | mate %d | %d | %d | %s | %s |" % (label, d, val, len(pv), need, verdict, bm))
        else:
            print("| %s | %d | %s %d | %d | - | %s | %s |" % (label, d, kind, val, len(pv), verdict, bm))
        sys.stdout.flush()
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=15)
    except Exception:
        p.kill()
