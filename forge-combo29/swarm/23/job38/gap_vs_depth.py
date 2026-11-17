#!/usr/bin/env python3
"""job38 : does the eval/go gap's STEP move with depth? (tests the cited sentence in 23-F80)

Board 1K6/8/8/3R4/8/8/8/k7 w (the F80 / 23-C26 board). For each (depth, counter) pair: run `eval` and
`go depth N`, report both and the gap. Onset = first counter at which go is cp 0 with every higher counter also cp 0.
"""
import re, subprocess, sys, os

EVAL_TOTAL = re.compile(r"info string eval .*?\btotal (-?\d+)")
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
FEN = "1K6/8/8/3R4/8/8/8/k7 w - - %d 1"
EXE = os.path.expanduser("~/build/forge")


def proc():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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


def evaltotal(p, fen):
    p.stdin.write("position fen " + fen + "\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("eval\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    val = None
    while True:
        s = p.stdout.readline().strip()
        m = EVAL_TOTAL.search(s)
        if m:
            val = int(m.group(1))
        if s == "readyok":
            break
    return val


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
            last = (m.group(2), int(m.group(3)), int(m.group(4)))
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    return last, bm


ROWS = []
print("| depth | counter | eval total | go score | go nodes | gap (cp) | bestmove |")
print("|---|---|---|---|---|---|---|")
for depth, counters in ((6, (80, 90, 93, 94, 95, 96, 98)), (12, (78, 84, 86, 87, 88, 89, 90))):
    for c in counters:
        fen = FEN % c
        p = proc()
        ev = evaltotal(p, fen)
        (score, val, nodes), bm = search(p, fen, depth)
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
        shown = "%s %d" % (score, val)
        gap = ev - val if score == "cp" else None
        ROWS.append((depth, c, ev, shown, nodes, gap, bm))
        print("| %d | %d | %s | %s | %d | %s | %s |" % (depth, c, ev, shown, nodes,
                                                       "-" if gap is None else gap, bm))
        sys.stdout.flush()

print()
for depth in (6, 12):
    sub = sorted([r for r in ROWS if r[0] == depth], key=lambda r: r[1])
    onset = None
    for i, r in enumerate(sub):
        if r[3] == "cp 0" and all(x[3] == "cp 0" for x in sub[i:]):
            onset = r[1]
            break
    spread = max(r[2] for r in sub) - min(r[2] for r in sub)
    print("depth %d: eval spread = %d cp; permanent cp-0 onset = %s" % (depth, spread, onset))
print()
print("P4 check (the step is depth-dependent, depth-6 onset at least 4 above depth-12 onset).")
