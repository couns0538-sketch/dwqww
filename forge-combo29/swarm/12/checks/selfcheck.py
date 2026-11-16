#!/usr/bin/env python3
"""selfcheck.py FORGE_EXE [--runs N] — one command: are MY Hash/MultiPV settings safe on THIS machine?

Why this exists: the Hash x MultiPV timings measured by seat 12 were taken on a 4-core cloud box.
The SHAPE of the effect (cost linear in Hash and in MultiPV-1) is a property of the code and
transfers anywhere; the absolute milliseconds are a property of the machine and do not. This script
lets the owner re-measure the four recommended settings on his own PC in about a minute.

It needs nothing but Python 3 and the engine binary. No python-chess, no pip.

Usage
    python selfcheck.py C:\\path\\to\\forge.exe
    python selfcheck.py /path/to/forge --runs 5 --threads 1

It runs, for each setting: a FRESH engine process, sends uci -> setoption Hash -> setoption MultiPV
-> setoption OwnBook false -> position -> isready -> `go depth 6`, and times from `go` to
`bestmove` with a monotonic clock. It reads every line up to `bestmove` before quitting (never
pipelines `quit`: an engine that is killed mid-search answers a fabricated first legal move with 0
nodes, which would time suspiciously well and mean nothing).

Output: median / min / max per setting, and a PASS / WATCH / FAIL verdict against thresholds that
are 4x the cloud-box numbers, because a machine 4x slower than that box is still playing fine.
"""
import queue
import re
import statistics
import subprocess
import sys
import threading
import time

FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# (label, Hash MB, MultiPV). The verdict is a RATIO against the cloud number, one rule for every
# cell, so no cell can "pass" merely because its budget is large:
#   PASS <= 4x, WATCH <= 10x, FAIL > 10x.
SETTINGS = [
    ("MultiPV 2, Hash  16", 16, 2),
    ("MultiPV 2, Hash  64", 64, 2),
    ("MultiPV 4, Hash  64", 64, 4),
    ("MultiPV 2, Hash 256", 256, 2),
]
PASS_RATIO, WATCH_RATIO = 4.0, 10.0
# An ABSOLUTE floor beside the ratio: a ratio alone lets a huge budget excuse a slow search
# (901 ms "passed" at Hash 256 because its 4x line is 1000 ms). For interactive analysis nothing
# here should take a second at depth 6, whatever the ratio says.
SLOW_MS = 500.0
# The coordinator's own reference point, named so the reader can check it directly:
#   "MultiPV 2 at Hash 64 taking more than 200 ms" = a machine ~4x this cloud box.
CLOUD = {"MultiPV 2, Hash  16": 17, "MultiPV 2, Hash  64": 52,
         "MultiPV 4, Hash  64": 82, "MultiPV 2, Hash 256": 250}


def one_run(exe, hash_mb, multipv, threads, go="go depth 6", bound=120.0):
    cmd = exe if isinstance(exe, list) else [exe]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    q = queue.Queue()
    lines = []
    threading.Thread(target=lambda: ([q.put(l.rstrip("\n")) for l in p.stdout], q.put(None)),
                     daemon=True).start()

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait_for(pred, limit):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            try:
                ln = q.get(timeout=0.2)
            except queue.Empty:
                if p.poll() is not None:
                    return None
                continue
            if ln is None:
                return None
            lines.append(ln)
            if pred(ln):
                return ln
        return "TIMEOUT"

    send("uci")
    wait_for(lambda l: l == "uciok", 30)
    for name, value in (("Hash", hash_mb), ("MultiPV", multipv),
                        ("Threads", threads), ("OwnBook", "false")):
        send(f"setoption name {name} value {value}")
        send("isready")
        wait_for(lambda l: l == "readyok", 30)
    send(f"position fen {FEN}")
    send("isready")
    wait_for(lambda l: l == "readyok", 30)

    t0 = time.monotonic()
    send(go)
    bm = wait_for(lambda l: l.startswith("bestmove"), bound)
    wall = time.monotonic() - t0
    send("quit")
    try:
        p.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()

    answered = isinstance(bm, str) and bm.startswith("bestmove")
    infos = sum(1 for l in lines if l.startswith("info depth"))
    reported = None
    for l in lines:
        if l.startswith("info depth"):
            m = re.search(r" nodes (\d+)", l)
            if m:
                reported = int(m.group(1))
    # A run with no info line is not a fast run, it is a run that never searched.
    return {"ms": wall * 1000, "answered": answered, "info_lines": infos,
            "reported": reported, "bestmove": bm.split()[1] if answered else None}



# ---------------------------------------------------------------------------------------------
# THE ANCHOR'S REFERENCE MEASUREMENT, and what it does and does not tell you.
#
# Measured on the reference box (4 cores, go nodes 1000000 -> 920,173 reported nodes):
#     median 604 ms per million reported nodes over 10 runs, range 591..633 (stdev 13, spread 7%)
#
# CORE COUNT WAS MEASURED AND DOES NOT MATTER for this anchor, because a Threads 1 search uses one
# core: pinning the process to ONE core gave 601 ms/M against 594 unpinned (within run-to-run noise),
# and running four engines at once on the four cores gave 553 ms/M against 543 idle (1.0x).
# So a 2-core, 4-core or 8-core machine of the SAME generation should land in the same band.
#
# What DOES move it: CPU generation, clock and cache. I have no second machine to measure, so I do
# NOT claim a number for a different generation. The band below is the honest envelope:
# run-to-run noise plus a modest allowance for a slower same-class CPU.
CLOUD_MS_PER_M_NODES = 600.0      # the reference value the ratio is taken against
REFERENCE_RANGE = (560, 700)      # "same class of machine" band, ms per million reported nodes
# ---------------------------------------------------------------------------------------------
ANCHOR_NODES = 1000000


def machine_speed(exe, threads, runs=3):
    """Absolute machine-speed anchor: a fixed NODE count, so the work is identical everywhere.

    This is independent of Hash and MultiPV, which is why it is a better absolute check than any
    depth-6 wall time: a depth search's work varies with pruning, a node count does not.
    """
    ms = []
    reported = None
    for _ in range(runs):
        r = one_run(exe, 16, 1, threads, go=f"go nodes {ANCHOR_NODES}", bound=300)
        if not r["answered"] or r["info_lines"] == 0 or not r.get("reported"):
            continue
        ms.append(r["ms"])
        reported = r["reported"]
    if not ms:
        return None
    med = statistics.median(ms)
    # use the REPORTED node count: `go nodes N` stops short of N (measured 92% at N=1e6),
    # so dividing by the request would understate the machine by 8%.
    per_m = med / (reported / 1e6)
    return {"median_ms": med, "reported": reported, "ms_per_m": per_m,
            "ratio": per_m / CLOUD_MS_PER_M_NODES, "runs": len(ms)}


def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="Are my Hash/MultiPV settings safe on THIS machine?",
        epilog="The engine takes no command-line arguments; this script feeds it on stdin.")
    ap.add_argument("engine", nargs="+",
                    help="path to the engine binary (put it after `--` if the path is odd)")
    ap.add_argument("--runs", type=int, default=5, help="fresh processes per setting (default 5)")
    ap.add_argument("--threads", type=int, default=1, help="Threads value to set (default 1)")
    ns = ap.parse_args()
    exe = ns.engine if len(ns.engine) > 1 else ns.engine[0]
    runs, threads = ns.runs, ns.threads

    print(f"engine : {exe}")
    print(f"runs   : {runs} fresh processes per setting, Threads {threads}, position startpos")
    print(f"search : go depth 6\n")

    # sanity: does this binary respond at all? an exit code of 0 with no output is not a result
    try:
        probe = one_run(exe, 16, 1, threads, go="go depth 1")
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"FATAL: could not run the engine: {exc}")
        return 1
    if not probe["answered"]:
        print("FATAL: the engine did not answer `go depth 1`.")
        print("  It takes no command-line arguments; this script feeds it on stdin.")
        print("  Check the path, and that this is the engine you meant to test.")
        return 1

    print(f"{'setting':22} {'cloud':>7} {'median':>8} {'min':>7} {'max':>7} "
          f"{'ratio':>7} {'runs':>5}  {'verdict'}")
    print("-" * 82)
    worst = 0
    grid_ratios = []
    for label, h, mpv in SETTINGS:
        ms, bad = [], 0
        for _ in range(runs):
            r = one_run(exe, h, mpv, threads)
            if not r["answered"] or r["info_lines"] == 0:
                bad += 1
                continue
            ms.append(r["ms"])
        if bad or not ms:
            print(f"{label:22} {CLOUD[label]:>5}ms {'--':>8} {'--':>7} {'--':>7} {'--':>7} "
                  f"{bad:>5}  FAIL (no completed search)")
            worst = max(worst, 3)
            continue
        med = statistics.median(ms)
        ratio = med / CLOUD[label]
        grid_ratios.append(ratio)
        if ratio <= PASS_RATIO:
            verdict = "PASS (within 4x)"
        elif ratio <= WATCH_RATIO:
            verdict = f"WATCH ({ratio:.1f}x the cloud box, usable)"
        else:
            verdict = f"FAIL ({ratio:.1f}x the cloud box)"
        if med > SLOW_MS and not verdict.startswith("FAIL"):
            # fine relative to this box, but too slow to sit and watch at depth 6
            verdict = f"SLOW ({med:.0f} ms absolute, {ratio:.1f}x)"
        worst = max(worst, 0 if verdict.startswith("PASS") else
                    (1 if (verdict.startswith("WATCH") or verdict.startswith("SLOW")) else 3))
        print(f"{label:22} {CLOUD[label]:>5}ms {med:>6.0f}ms {min(ms):>5.0f}ms "
              f"{max(ms):>5.0f}ms {ratio:>6.1f}x {runs - bad:>5}  {verdict}")

    # ---- the ABSOLUTE anchor, independent of Hash and MultiPV
    print()
    print("=== absolute machine-speed anchor (fixed node count, not a ratio of a depth search)")
    speed = machine_speed(exe, threads)
    abs_verdict = None
    if speed is None:
        print("  could not measure: no completed search")
        abs_verdict = "unknown"
    else:
        abs_verdict = ("PASS" if speed["ratio"] <= PASS_RATIO else
                       "WATCH" if speed["ratio"] <= WATCH_RATIO else "FAIL")
        lo, hi = REFERENCE_RANGE
        in_band = lo <= speed["ms_per_m"] <= hi
        print(f"  `go nodes {ANCHOR_NODES:,}` -> {speed['reported']:,} reported nodes in "
              f"{speed['median_ms']:.0f} ms  =  {speed['ms_per_m']:,.0f} ms per million nodes")
        print(f"  reference box (4 cores, measured): {CLOUD_MS_PER_M_NODES:,.0f} ms per million")
        print(f"  same-class band                  : {lo}-{hi} ms per million"
              f"   -> your machine is {speed['ratio']:.2f}x the reference"
              f"   [{'in band' if in_band else 'OUTSIDE the band'}]")
        print(f"  core count does NOT move this anchor (a Threads 1 search uses one core: measured")
        print(f"  601 ms/M pinned to 1 core vs 594 unpinned). CPU generation and clock do.")
        if speed["ms_per_m"] < lo:
            print(f"  Your CPU is FASTER than the reference box. The band is not a limit above --")
            print(f"  faster is good, and the grid's PASS lines still apply unchanged.")
        elif speed["ms_per_m"] > hi:
            print(f"  Your CPU is SLOWER than the reference class. The band cannot tell you whether")
            print(f"  that is normal for your CPU or something is wrong: I have no second machine to")
            print(f"  measure, so I do not claim a number for your generation. Treat the ANCHOR as")
            print(f"  comparable only to this reference measurement, scale the grid's thresholds by")
            print(f"  {speed['ratio']:.1f}x, and prefer smaller Hash / fewer PV lines.")

    print()
    print("How to read this")
    print("  cloud = median on the 4-core machine these tables came from; ratio = yours / cloud.")
    print("  PASS  = within 4x. A machine 4x slower is still fine to play with.")
    print("  WATCH = 4x to 10x. Usable; prefer one notch smaller Hash if a search feels slow.")
    print("  FAIL  = over 10x, or a run that never completed a search.")
    print(f"  SLOW  = within {WATCH_RATIO:.0f}x but over {SLOW_MS:.0f} ms absolute at depth 6: your")
    print("          machine is fine, this setting is just slow to watch. Drop a notch.")
    print("  Reference point: MultiPV 2 at Hash 64 over 200 ms means a machine about 4x this one.")
    print()
    print("WHICH VERDICT TO TRUST WHEN THEY DISAGREE")
    print("  The anchor measures the machine and nothing else; the grid measures the settings on")
    print("  that machine. If the anchor is PASS and a grid cell FAILs, the setting is the problem,")
    print("  not the machine: use a smaller Hash or fewer PV lines.")
    print("  If the anchor is WATCH/FAIL and the grid cells are PASS, trust the ANCHOR: the grid")
    print("  numbers are relative to this cloud box, and a uniformly slower machine can still")
    print("  finish a depth-6 search quickly while being slow at everything else.")
    print("  If both agree, trust both.")
    if speed is not None:
        grid_worst = max((c for c in grid_ratios), default=1.0)
        if speed["ratio"] < 1.0 and grid_worst > PASS_RATIO:
            print()
            print("  ** INCOHERENT: the anchor calls this machine FASTER than the cloud box while")
            print(f"     the grid finds a cell {grid_worst:.1f}x slower. That combination is not")
            print("     physically plausible for one binary. Most likely the engine misreports its")
            print("     node count (the anchor divides by the REPORTED count), so trust the GRID")
            print("     numbers here and treat the anchor as unmeasured.")
    print()
    print("The SHAPE is what matters and it does not depend on your machine:")
    print("  MultiPV 1 costs the same at every Hash size; the cost is (MultiPV-1) x Hash.")
    print("  So if a cell here is slow, halving Hash or dropping one MultiPV line fixes it.")
    print()
    print("The one setting that is never safe on any machine: Hash 2048 with MultiPV 8")
    print("  (8-9 s for `go depth 6`, depth 0-1 on a 5 s clock, on the cloud box).")
    anchor_bad = 0 if abs_verdict in ("PASS", None) else (1 if abs_verdict == "WATCH" else 3)
    worst = max(worst, anchor_bad)
    return 0 if worst == 0 else (1 if worst == 1 else 2)


if __name__ == "__main__":
    sys.exit(main())
