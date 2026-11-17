#!/usr/bin/env python3
"""repro_illegal_move.py : 23-F95 repro that does NOT fall into 19-F12.

The first version of this repro piped the UCI stream from a file, so stdin hit EOF right after `go depth 8` and the
engine aborted with `bestmove` and ZERO info lines — the 19-F12 quit/EOF fault, not the illegal-move effect. Any
node count read from that run would have been fabricated. This driver keeps stdin OPEN and drains stdout to
`bestmove`, which is the convention this seat established after 19-F12.

Prints, for each case: the info lines seen, the final score and node count, and the bestmove.
Case A: legal move list (control)      -> must show a real search.
Case B: list with an illegal move at ply 7 -> the subject of 23-F95.
"""
import re, subprocess, sys, os

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
ENGINE = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/build/forge")
FEN = "1K6/8/8/3R4/8/8/8/k7 b - - 0 1"
LEGAL = "a1b1 d5d6 b1a1 d6d5 a1b1 d5d6 b1a1"          # 7 legal plies (validated in python-chess)
ILLEGAL = "a1b1 d5d6 b1a1 d6d5 a1b1 d5d6 a1b1 d6d5"    # ply 7 a1b1 is illegal


def run(moves, depth=8):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    opts = set()
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
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n" % (FEN, moves)); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    strings = []
    while True:
        s = p.stdout.readline().strip()
        if s.startswith("info string"):
            strings.append(s)
        if s == "readyok":
            break
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    infos = 0
    last = None
    while True:
        l = p.stdout.readline()
        if not l:
            raise RuntimeError("died in search (stdin was held open, so this is not 19-F12)")
        s = l.strip()
        if s.startswith("info string"):
            strings.append(s)
        m = INFO.match(s)
        if m:
            infos += 1
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return infos, last, bm, strings


print("engine:", ENGINE)
print("board : %s" % FEN)
print()
for label, moves in (("A  LEGAL 7-ply list (control)", LEGAL), ("B  list with illegal move at ply 7", ILLEGAL)):
    infos, last, bm, strings = run(moves)
    print("%s" % label)
    print("   moves   : %s" % moves)
    print("   strings : %s" % (strings if strings else "(none)"))
    print("   info lines: %d | last score %s %s | nodes %s | bestmove %s" % (
        infos, last[0], last[1], last[2], bm) if last else "   info lines: %d | NO SCORE | bestmove %s" % (infos, bm))
    print()
print("READ: if case B shows info lines and a node count comparable to case A, the engine DID search a position —")
print("the one reached by the legal prefix — despite the illegal move, which is 23-F95. If case B shows ZERO info")
print("lines, the driver has fallen into 19-F12 and no conclusion may be drawn.")
