#!/usr/bin/env python3
"""Recheck the four honesty pins, and the `go infinite` control the brief calls out.

Pins (section 2 and the PCBUILD table):
    bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609

Each is measured in a FRESH process, Threads 1, Hash 16, and every reply is scanned for
`info string invalid FEN` before it is parsed.

The `go infinite` case is included because the brief states it as a measured failure: on a real
position `go infinite` does not stop by itself, so a STOP is required.  This script asserts that
a bare `go infinite` produces NO bestmove within a bounded window, and that `stop` then produces
one -- if the first assertion ever fails, the script says so rather than silently passing.
"""
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "build/forge"
PINS = {11: 312866, 13: 862329, 16: 3024920}
PERFT5 = 4865609


def fresh(script, wait_for, timeout=900.0):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []
    deadline = time.monotonic() + timeout

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    while time.monotonic() < deadline:
        ln = p.stdout.readline()
        if ln == "":
            break
        lines.append(ln.rstrip("\n"))
        if ln.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for entry in script:
        send(entry)
        while time.monotonic() < deadline:
            ln = p.stdout.readline()
            if ln == "":
                break
            lines.append(ln.rstrip("\n"))
            if wait_for(lines[-1]):
                break
        else:
            break
    send("quit")
    try:
        p.wait(timeout=60)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


rows = 0
agree = 0
bad = []

for depth, want in sorted(PINS.items()):
    # `bench` prints `info string bench depth N nodes X time Y nps Z` and NO `bestmove`.
    # Waiting for a bestmove here blocked until the wall timeout; the terminator is the bench line.
    lines = fresh(["bench %d" % depth],
                  lambda ln: ln.startswith("info string bench depth"))
    fen_bad = [ln for ln in lines if "invalid FEN" in ln]
    got = None
    for ln in lines:
        if ln.startswith("info string bench depth"):
            tok = ln.split()
            if "nodes" in tok:
                got = int(tok[tok.index("nodes") + 1])
    rows += 1
    ok = (got == want) and not fen_bad
    agree += 1 if ok else 0
    if not ok:
        bad.append("bench %d: got %r want %d (invalid-FEN lines: %d)" % (depth, got, want, len(fen_bad)))
    print("  bench %-2d  got %-9r want %-9d %s" % (depth, got, want, "OK" if ok else "MISMATCH"))

lines = fresh(["position startpos", "isready", "go perft 5"], lambda ln: ln.startswith("nodes "))
fen_bad = [ln for ln in lines if "invalid FEN" in ln]
got = None
for ln in lines:
    if ln.startswith("nodes "):
        got = int(ln.split()[-1])
rows += 1
ok = (got == PERFT5) and not fen_bad
agree += 1 if ok else 0
if not ok:
    bad.append("perft 5: got %r want %d" % (got, PERFT5))
print("  perft 5  got %-9r want %-9d %s" % (got, PERFT5, "OK" if ok else "MISMATCH"))

# --- go infinite control ---------------------------------------------------
p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)


def snd(s):
    p.stdin.write(s + "\n")
    p.stdin.flush()


snd("uci")
while p.stdout.readline().strip() != "uciok":
    pass
snd("setoption name Threads value 1")
snd("setoption name Hash value 16")
snd("position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
snd("isready")
while p.stdout.readline().strip() != "readyok":
    pass
snd("go infinite")
stopped_by_itself = False
deadline = time.monotonic() + 3.0
while time.monotonic() < deadline:
    p.stdout.flush()
    ln = p.stdout.readline()
    if ln == "":
        break
    if ln.startswith("bestmove"):
        stopped_by_itself = True
        break
snd("stop")
got_bestmove = False
deadline = time.monotonic() + 20.0
while time.monotonic() < deadline:
    ln = p.stdout.readline()
    if ln == "":
        break
    if ln.startswith("bestmove"):
        got_bestmove = True
        break
snd("quit")
try:
    p.wait(timeout=30)
except subprocess.TimeoutExpired:
    p.kill()

rows += 1
ok = (not stopped_by_itself) and got_bestmove
agree += 1 if ok else 0
if not ok:
    bad.append("go infinite: stopped_by_itself=%s, stop produced bestmove=%s"
               % (stopped_by_itself, got_bestmove))
print("  go infinite: bestmove without stop=%s | after stop=%s  %s"
      % (stopped_by_itself, got_bestmove, "OK" if ok else "MISMATCH"))

print("\nrows examined: %d" % rows)
print("agree: %d / %d" % (agree, rows))
if bad:
    print("DISAGREEMENTS:")
    for b in bad:
        print("  - %s" % b)
sys.exit(0 if not bad else 1)
