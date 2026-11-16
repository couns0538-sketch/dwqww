#!/usr/bin/env python3
"""S02 probe: does `go wtime 100` (clock for the side that is NOT to move) ever terminate by itself?

The job-1 v3 run flagged 9 sequences where `go wtime 100` produced no bestmove within 20 s. Two possible
causes, and they are very different:
  (a) the engine treats a clock given only for the side not to move as "no time limit" and searches until
      stopped, or
  (b) my driver mis-classified the command (it must then be stopped by the driver like an unbounded go).

This probe answers that without a driver in the way: one reader thread, no stop sent for WAIT s, then a
count of bestmove lines seen, then stop.

usage: probe_clock.py <exe>
"""
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/base/forge-combo29/build/forge"
WAIT = 3.0
START_W = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
START_B = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
MID = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"


def probe(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines, lock = [], threading.Lock()

    def reader():
        for line in p.stdout:
            with lock:
                lines.append(line.rstrip("\n"))

    threading.Thread(target=reader, daemon=True).start()

    def say(text):
        p.stdin.write(text + "\n")
        p.stdin.flush()

    say("uci")
    say("isready")
    say("setoption name OwnBook value false")
    say("position fen " + fen)
    time.sleep(0.3)
    n_before = len(lines)
    t0 = time.monotonic()
    say(go)
    time.sleep(WAIT)
    with lock:
        seg = list(lines[n_before:])
    own = [l for l in seg if l.startswith("bestmove")]
    elapsed = time.monotonic() - t0
    say("stop")
    time.sleep(0.4)
    with lock:
        seg2 = list(lines[n_before:])
    after = [l for l in seg2 if l.startswith("bestmove")]
    info = [l for l in seg2 if l.startswith("info depth")]
    say("quit")
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return {"fen": fen, "go": go, "bestmove_within_wait": own, "wait_s": WAIT,
            "bestmove_after_stop": [l for l in after if l not in own],
            "info_depth_lines": len(info), "elapsed_s": round(elapsed, 3),
            "first_info": (info[0][:70] if info else None)}


CASES = [
    (START_W, "go wtime 100"),
    (START_W, "go wtime 100 btime 100"),
    (START_W, "go btime 100"),
    (START_B, "go btime 100"),
    (START_B, "go wtime 100 btime 100"),
    (START_W, "go wtime 100 winc 10 binc 10"),
    (START_W, "go movestogo 1 wtime 100"),
    (MID, "go wtime 100"),
    (START_W, "go movetime 100"),
]

print("| position | go | bestmove within %.0f s on its own | bestmove only after stop | info depth lines |" % WAIT)
print("|---|---|---|---|---|")
bad = 0
for fen, go in CASES:
    r = probe(fen, go)
    label = "start, White to move" if fen == START_W else ("start, Black to move" if fen == START_B else "middlegame, White")
    print("| %s | `%s` | %s | %s | %d |" % (
        label, go, bool(r["bestmove_within_wait"]), bool(r["bestmove_after_stop"]), r["info_depth_lines"]))
    if not r["bestmove_within_wait"]:
        bad += 1
print()
print("searches that did not terminate by themselves: %d of %d" % (bad, len(CASES)))
