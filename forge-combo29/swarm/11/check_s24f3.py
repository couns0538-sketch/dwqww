#!/usr/bin/env python3
"""check_s24f3.py EXE — seat 11's INDEPENDENT check of seat 24's 24-F3.

24-F3 claims: G position 90 `5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1` is a ~1000x WARM-STATE
search-time outlier: hundreds of seconds inside a long-lived TSan process, versus 0.8-2.0 s in
FRESH TSan processes and 0.1 s in the release build.

I cannot afford 348 s, and the claim is about TSan (their build). What I CAN test, cheaply and
on the release build, is the part that would make the claim actionable: does the SAME position
behave differently warm vs cold ON THE RELEASE BUILD? If it does not, the effect is specific to
their instrumented build, which is important scope for the owner.

Method: cold = fresh process, one `go depth 12`; warm = one process, search 40 other G positions
first, then position 90. Time both with a monotonic clock, several repetitions.
Predictions stated up front:
  P1. the release build answers position 90 at depth 12 in under 10 s cold (they measured ~0.1 s)
  P2. warm/cold on release differ by less than 10x
  P3. if either fails, the outlier is a TSan-only effect on MY machine
"""
import os, subprocess, sys, time

EXE = sys.argv[1]
FEN90 = "5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"
G = "/agent/repos/dwqww/forge-combo29/swarm/11/positions/G_set_G.epd"


def cold_run(depth=12, timeout=120):
    inp = f"uci\nisready\nposition fen {FEN90}\nisready\ngo depth {depth}\n"
    t0 = time.monotonic()
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write(inp); p.stdin.flush()
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
        if time.monotonic() - t0 > timeout:
            break
    el = time.monotonic() - t0
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception:
        p.kill()
    return el, bm


def warm_run(fillers=40, depth=12, timeout=180):
    """One process; search `fillers` other G positions, then position 90."""
    fens = []
    with open(G) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                fens.append(line.split(";")[0].strip().split(" ")[:6])
    fens = [" ".join(x) for x in fens if len(x) == 6 and "5R2/1p5k/6p1" not in x][:fillers]

    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write("uci\nisready\n"); p.stdin.flush()
    while True:
        line = p.stdout.readline()
        if line.strip() == "uciok":
            break
    for fen in fens:
        p.stdin.write(f"position fen {fen}\nisready\ngo depth 12\n"); p.stdin.flush()
        while True:
            line = p.stdout.readline()
            if not line or line.startswith("bestmove"):
                break
    t0 = time.monotonic()
    p.stdin.write(f"position fen {FEN90}\nisready\ngo depth {depth}\n"); p.stdin.flush()
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
        if time.monotonic() - t0 > timeout:
            break
    el = time.monotonic() - t0
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception:
        p.kill()
    return el, bm


print(f"exe {EXE}")
print(f"position 90: {FEN90}")
print("\ncold (fresh process each time):")
colds = []
for i in range(3):
    el, bm = cold_run()
    colds.append(el)
    print(f"  run {i+1}: {el:.2f}s  bestmove {bm}")
print("\nwarm (40 other G searches first, same process):")
warms = []
for i in range(2):
    el, bm = warm_run()
    warms.append(el)
    print(f"  run {i+1}: {el:.2f}s  bestmove {bm}")

c = min(colds); w = min(warms)
print(f"\nfastest cold {c:.2f}s, fastest warm {w:.2f}s, ratio {w/c:.2f}x")
print("\n=== verdict ===")
print(f"  P1 (cold under 10 s on release): {'PASS' if c < 10 else 'FAIL'}")
print(f"  P2 (warm within 10x of cold):    {'PASS' if w/c < 10 else 'FAIL'}")
print("\nI do NOT reproduce seat 24's 348 s figure and make no claim about their TSan build;")
print("this check only says whether the outlier exists on an uninstrumented release build here.")
