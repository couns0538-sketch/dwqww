#!/usr/bin/env python3
"""S02 — S-F7 threshold grid + fixed-depth latency. The deliverable the owner asked for.

Two questions, both answered by one run:
  (1) At which Hash size and MultiPV value does the collapse begin, on a 5-second clock?
      Grid: Hash in {16, 64, 256, 2048} x MultiPV in {2, 3, 5, 8}, reporting the depth actually reached.
      MultiPV 1 is included as the reference row for every Hash size, because "safe" only means something
      against a baseline measured in the same conditions.
  (2) Does the collapse also happen at a FIXED DEPTH, where a clock cannot be exhausted?
      `go depth 12` at Hash 16 vs Hash 2048 with MultiPV 8. If the fixed-depth search is also slow, the defect
      is a latency problem for batch analysis, not only a clock problem.

Conditions held constant, and stated because they define the numbers:
  * Threads 1 on every run (seat 04: scores above Threads 1 are not reproducible).
  * OwnBook false, so a book answer cannot masquerade as a fast search.
  * the PC r15 build (the engine the owner plays), release.
  * fresh process per cell, interactive driver (19-F12), COLD (seat 10).
  * 3 runs per cell for the clock grid, so a single lucky or unlucky run cannot set the answer;
    the median depth and the full list are both printed.

usage: s_f7_grid.py <pc_exe> <outdir>
"""
import json
import os
import stat
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_grid"

HASHES = [16, 64, 256, 2048]
MULTIPVS = [1, 2, 3, 5, 8]
CLOCK = "go wtime 5000 btime 5000"
FIXED_DEPTH = "go depth 12"
RUNS = 3
SETUP_COMMON = ["setoption name Threads value 1", "setoption name OwnBook value false"]


def one_run(exe, hash_mb, multipv, go, cap_s=60.0):
    """One fresh engine, one search. Returns (ms, deepest depth seen, bestmove, info line count)."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=10.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        p.kill()
        raise SystemExit("FAIL: no uciok")
    send("setoption name Hash value %d" % hash_mb)
    for s in SETUP_COMMON:
        send(s)
    send("setoption name MultiPV value %d" % multipv)
    send("isready")
    if not wait("readyok"):
        p.kill()
        raise SystemExit("FAIL: no readyok after setup for Hash %d MultiPV %d" % (hash_mb, multipv))
    # a refused option would invalidate the cell silently — check before measuring
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            p.kill()
            raise SystemExit("FAIL: option refused (%r) for Hash %d MultiPV %d" % (line, hash_mb, multipv))
    send("position startpos")
    send("isready")
    n = len(L)
    wait("readyok", n)
    n = len(L)
    t0 = time.monotonic()
    send(go)
    got = wait("bestmove", n, cap_s)
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n:])
    if not got:
        send("stop")
        wait("bestmove", n, 10.0)
        seg = list(L[n:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    depths = []
    for line in seg:
        if line.startswith("info depth "):
            try:
                depths.append(int(line.split()[2]))
            except (IndexError, ValueError):
                pass
    bm = [l for l in seg if l.startswith("bestmove")]
    return {"ms": round(ms, 0), "max_depth": max(depths) if depths else 0,
            "info_lines": len(depths), "bestmove": bm[-1].split()[1] if bm else None,
            "ended_by_itself": got}


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {
        "exe": EXE,
        "sha256": subprocess.run(["sha256sum", EXE], capture_output=True, text=True).stdout.split()[0],
        "build": "PC r15 (base 6b98f217 + FABLE_TO_swarm_5 patch), release",
        "threads": 1,
        "option_lines_sent": SETUP_COMMON + ["setoption name Hash value <H>",
                                             "setoption name MultiPV value <M>"],
        "clock_search": CLOCK, "fixed_depth_search": FIXED_DEPTH,
        "runs_per_cell": RUNS, "position": "startpos",
        "driver": "interactive, fresh process per cell, COLD; a refused option aborts the cell",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    # ---------- (1) the clock grid ----------
    grid = {}
    print("== clock grid: %s, threads 1, %d runs per cell" % (CLOCK, RUNS))
    print("%-10s %s" % ("Hash\\MPV", "  ".join("MPV %-2d" % m for m in MULTIPVS)))
    for h in HASHES:
        cells = []
        for m in MULTIPVS:
            runs = [one_run(EXE, h, m, CLOCK) for _ in range(RUNS)]
            depths = [r["max_depth"] for r in runs]
            times = [r["ms"] for r in runs]
            cell = {"hash": h, "multipv": m, "depths": depths, "ms": times,
                    "median_depth": median(depths), "median_ms": median(times)}
            grid["%d_%d" % (h, m)] = cell
            cells.append("d%-2d/%5.0fms" % (median(depths), median(times)))
            print("  Hash %-5d MPV %-2d -> depths %s  times %s"
                  % (h, m, depths, times), flush=True)
        print("%-10d %s" % (h, "  ".join("%-12s" % c for c in cells)), flush=True)

    print()
    print("### TABLE 1 — depth reached on a 5-second clock (median of %d runs), PC r15, Threads 1" % RUNS)
    print()
    print("| Hash \\ MultiPV | " + " | ".join("MultiPV %d" % m for m in MULTIPVS) + " |")
    print("|---|" + "---|" * len(MULTIPVS))
    for h in HASHES:
        row = []
        for m in MULTIPVS:
            c = grid["%d_%d" % (h, m)]
            row.append("**d%d** (%.0f ms)" % (c["median_depth"], c["median_ms"]))
        print("| **%d MB** | %s |" % (h, " | ".join(row)))

    print()
    print("### TABLE 2 — wall time on the same 5-second clock (median of %d runs)" % RUNS)
    print()
    print("| Hash \\ MultiPV | " + " | ".join("MultiPV %d" % m for m in MULTIPVS) + " |")
    print("|---|" + "---|" * len(MULTIPVS))
    for h in HASHES:
        row = []
        for m in MULTIPVS:
            c = grid["%d_%d" % (h, m)]
            row.append("%.0f ms" % c["median_ms"])
        print("| **%d MB** | %s |" % (h, " | ".join(row)))

    # ---------- (2) fixed depth: no clock to exhaust ----------
    print()
    print("== fixed depth: %s (no clock, so a collapse here is pure latency)" % FIXED_DEPTH)
    fixed = {}
    for h, m in ((16, 1), (16, 8), (256, 8), (2048, 1), (2048, 8)):
        runs = [one_run(EXE, h, m, FIXED_DEPTH) for _ in range(RUNS)]
        fixed["%d_%d" % (h, m)] = {
            "hash": h, "multipv": m,
            "ms": [r["ms"] for r in runs],
            "median_ms": median([r["ms"] for r in runs]),
            "depth": [r["max_depth"] for r in runs],
            "info_lines": [r["info_lines"] for r in runs],
        }
        print("  Hash %-5d MPV %-2d -> %s ms, depth %s, %s info lines"
              % (h, m, [r["ms"] for r in runs], [r["max_depth"] for r in runs],
                 [r["info_lines"] for r in runs]), flush=True)
    print()
    print("### TABLE 3 — %s, wall time (median of %d runs) — a fixed-depth search cannot 'run out of clock'" % (FIXED_DEPTH, RUNS))
    print()
    print("| Hash | MultiPV | median ms | depth | info lines |")
    print("|---|---|---|---|---|")
    for k in ("16_1", "16_8", "256_8", "2048_1", "2048_8"):
        f = fixed[k]
        print("| %d MB | %d | **%.0f ms** | %d | %d |"
              % (f["hash"], f["multipv"], f["median_ms"],
                 fixed[k]["depth"][0], fixed[k]["info_lines"][0]))

    json.dump({"grid": grid, "fixed": fixed}, open(os.path.join(OUT, "grid.json"), "w"), indent=1)
    print()
    print("raw: grid.json, meta.json")


if __name__ == "__main__":
    main()
