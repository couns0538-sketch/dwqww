#!/usr/bin/env python3
"""job42 : is a short mate PV a TRUNCATED LINE or a WRONG DISTANCE? Replays every PV, reports 2M-1 shape.

Usage: python3 distance_or_truncation.py <exe> <fen> <depth> [<depth> ...]
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+).*?(?: pv(?: (.+))?)?\s*$")


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
    if b.is_checkmate():
        return "MATE", len(moves)
    return "NO-MATE", len(moves)


exe = os.path.expanduser(sys.argv[1])
fen = sys.argv[2]
depths = [int(x) for x in sys.argv[3:]]
p = proc(exe)
print("fen: %s" % fen)
print("| depth | score | pv plies | replay | 2N-1 (N=score) | pv len = 2M-1 for M = | bestmove |")
print("|---|---|---|---|---|---|---|")
for d in depths:
    info, bm = search(p, fen, d)
    if info is None:
        print("| %d | PARSE FAILURE | - | - | - | - | %s |" % (d, bm))
        continue
    depth, kind, val, nodes, pv = info
    verdict, nply = replay(fen, pv)
    need = 2 * val - 1 if kind == "mate" and val > 0 else None
    implied = ((nply + 1) // 2) if (nply and nply % 2 == 1) else None
    # check whether the PV itself is a legal completed line whose length fits some M
    line = "| %d | %s %d | %d | %s | %s | %s | %s |" % (
        depth, kind, val, len(pv), verdict, need, implied if implied else "not odd", bm)
    print(line)
    print("   pv: " + " ".join(pv))
    sys.stdout.flush()
p.stdin.write("quit\n"); p.stdin.flush()
