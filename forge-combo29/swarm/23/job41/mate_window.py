#!/usr/bin/env python3
"""job41 : sweep the mate-with-truncated-PV window across three won boards and a drawn control, both builds.

For every `mate N` cell: replay the PV in python-chess, report PV plies, plies needed (2N-1), and whether the replay
ends in MATE. Control: the drawn board must report NO mate cell on either build.
"""
import re, subprocess, sys, os
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+).*?(?: pv(?: (.+))?)?\s*$")

BOARDS = [("W1 K+RvK", "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"),
          ("W2 K+QvK", "8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
          ("W3 K+RvK c60", "1K6/8/8/3R4/8/8/8/k7 w - - 60 1"),
          ("DRAWN Kvhk", "8/8/8/8/8/8/8/K6k w - - 0 1")]
DEPTHS = (8, 10, 12, 14, 16, 18)
BUILDS = (("base", os.path.expanduser("~/build/forge")),
          ("PC r15", os.path.expanduser("~/pcbuild/forge")))


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
            pvtext = m.group(5) or ""
            last = (int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4)), pvtext.split())
        if s.startswith("bestmove"):
            return last


def replay(fen, moves):
    b = chess.Board(fen)
    for mv in moves:
        try:
            m = chess.Move.from_uci(mv)
        except Exception:
            return "BAD-TOKEN"
        if m not in b.legal_moves:
            return "ILLEGAL"
        b.push(m)
    return "MATE" if b.is_checkmate() else "NO-MATE"


print("| board | build | depth | score | pv plies | needs | replay |")
print("|---|---|---|---|---|---|---|")
MATE_CELLS = []
PARSED = {"n": 0}
for label, fen in BOARDS:
    for name, exe in BUILDS:
        p = proc(exe)
        for d in DEPTHS:
            info = search(p, fen, d)
            if info is None:
                print("| %s | %s | %d | **PARSE FAILURE** | - | - | - |" % (label, name, d))
                PARSED.setdefault("fail", []).append((label, name, d))
                print("HARD FAILURE: no info line parsed at %s %s depth %d" % (label, name, d))
                sys.stdout.flush()
                continue
            PARSED["n"] += 1
            depth, kind, val, nodes, pv = info
            if kind != "mate" or val <= 0:
                continue
            need = 2 * val - 1
            verdict = replay(fen, pv)
            MATE_CELLS.append((label, name, d, val, len(pv), need, verdict))
            print("| %s | %s | %d | mate %d | %d | %d | %s |" % (label, name, d, val, len(pv), need, verdict))
            sys.stdout.flush()
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=15)
        except Exception:
            p.kill()

print()
print("cells actually parsed: %d of %d" % (PARSED["n"], len(BOARDS) * len(BUILDS) * len(DEPTHS)))
if PARSED.get("fail"):
    print("HARD FAILURE: %d cells produced no parseable info line — the run is NOT complete and no")
    print("count below may be read as a result. Cells: %s" % (PARSED["fail"],))
bad = [c for c in MATE_CELLS if c[6] != "MATE"]
print("mate cells total: %d; cells whose PV does not mate: %d" % (len(MATE_CELLS), len(bad)))
for c in bad:
    print("  short: %s %s depth %d mate %d, pv %d plies, needs %d" % (c[0], c[1], c[2], c[3], c[4], c[5]))
print()
print("P1 at most two short depths per board/build.  P2 every depth-18 mate cell replays to MATE.")
print("P3 short cells are exactly 2 plies short (pv = 2N-3).  P4 no mate cell on the drawn board.")
