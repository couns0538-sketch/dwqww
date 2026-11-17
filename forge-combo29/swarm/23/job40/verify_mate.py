#!/usr/bin/env python3
"""job40b : verify the mate claims directly, by replaying each PV in python-chess and asserting it ends in mate.

A PV length that matches 2N-1 is only INTERNAL consistency. The real check: is every move legal, and does the last
one deliver checkmate? This also gives the known-answer control the mate claims needed — the same verifier must
accept a textbook mate (fool's mate) and must REJECT a truncated PV.

Usage: python3 verify_mate.py <exe> <fen> <depth> [...]
Prints the full PV, the replay result, and the mate distance the PV actually delivers.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+).*? pv (.+)$")


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


def search_pv(p, fen, depth):
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
            last = (int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)), m.group(5).split())
        if s.startswith("bestmove"):
            return last


def replay(fen, moves):
    b = chess.Board(fen)
    for i, mv in enumerate(moves):
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            return "ILLEGAL-TOKEN", mv, i
        if m not in b.legal_moves:
            return "ILLEGAL-MOVE", mv, i
        b.push(m)
    if b.is_checkmate():
        return "MATE", None, len(moves)
    return "NO-MATE", None, len(moves)


print("== control: the verifier must accept a real mate and reject a truncated one ==")
fool = chess.Board()
for mv in ("f2f3", "e7e5", "g2g4", "d8h4"):
    fool.push(chess.Move.from_uci(mv))
print("full fool's mate line ->", "MATE" if fool.is_checkmate() else "NOT-MATE")
short = chess.Board()
for mv in ("f2f3", "e7e5", "g2g4"):
    short.push(chess.Move.from_uci(mv))
print("truncated line        ->", "MATE" if short.is_checkmate() else "NO-MATE (correctly rejected)")
print()

exe = os.path.expanduser(sys.argv[1])
fen = sys.argv[2]
p = proc(exe)
for d in [int(x) for x in sys.argv[3:]]:
    info = search_pv(p, fen, d)
    depth, kind, val, nodes, pv = info
    verdict, bad, nply = replay(fen, pv)
    need = 2 * val - 1 if kind == "mate" and val > 0 else None
    print("depth %d: score %s %d  nodes %d  pv %d plies (needs %s)" % (depth, kind, val, nodes, len(pv), need))
    print("   pv: " + " ".join(pv))
    print("   replay: %s%s  (%d plies applied)" % (verdict, "" if bad is None else " at " + bad, nply))
p.stdin.write("quit\n"); p.stdin.flush()
