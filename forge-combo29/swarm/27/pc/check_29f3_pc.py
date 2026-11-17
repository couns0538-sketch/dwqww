#!/usr/bin/env python3
"""check_29f3_pc.py <exe> <outdir> [--settings PC20|S14|none]

Seat 29's 29-F3: a DEPTH-INDEPENDENT fixed cost sits inside every `bench N` timing (the Searcher is
constructed and its table cleared 8 times after the timer starts), so the `time` a bench reports
includes work that does not scale with depth, and nps from shallow benches is understated.

The test that distinguishes "fixed cost inside the timer" from "the bench is just slow at shallow
depth" is a LINEARITY check: if `time` has a constant part c plus a per-depth part k*nodes, then
plotting reported time against reported nodes must give a straight line whose INTERCEPT (at 0 nodes)
is the fixed cost. A bench with no fixed cost would pass through the origin.

I fit that line over several depths on the PC build, and repeat the whole thing twice to show the
spread. Threads 1, fresh process per bench, OwnBook false, one `go`-free `bench` (which is synchronous).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]


class Missing(Exception):
    pass


def bench(exe, settings, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=900):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("bench %d" % depth)
        lines, ok = until(lambda x: "info string bench depth" in x)
        if not ok:
            raise Missing("no bench line at depth %d" % depth)
        # GUARD (S-W1): this harness parses a BENCH line, not `info depth`, so it needs its own
        # emptiness check: if the bench line never arrived the row must abort, not record a None.
        bench_lines = [l for l in lines if "info string bench depth" in l]
        if not bench_lines:
            raise Missing("no 'info string bench depth' line (bench did not report; row aborted)")
        line = bench_lines[-1]
        m = re.search(r"bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)", line)
        if not m:
            raise Missing("bench line did not parse: %r" % line)
        return {"depth": int(m.group(1)), "nodes": int(m.group(2)),
                "time_ms": int(m.group(3)), "nps": int(m.group(4))}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def fit(depths, times):
    """Least squares times = a + b*depths. Returns intercept, slope, r2."""
    n = len(depths)
    md = sum(depths) / n
    mt = sum(times) / n
    sxx = sum((d - md) ** 2 for d in depths)
    sxy = sum((d - md) * (t - mt) for d, t in zip(depths, times))
    b = sxy / sxx
    a = mt - b * md
    ss_tot = sum((t - mt) ** 2 for t in times)
    ss_res = sum((t - (a + b * d)) ** 2 for d, t in zip(depths, times))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return a, b, r2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--depths", default="10,11,12,13,14")
    ap.add_argument("--rounds", type=int, default=2)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    depths = [int(x) for x in a.depths.split(",")]
    settings = {"none": ["Hash 16", "Threads 1"],
                "S14": ["Hash 16", "Threads 1"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    rounds = []
    for r in range(a.rounds):
        rows = [bench(exe, settings, d) for d in depths]
        # fit reported time against NODES (the work), which is the right x-axis for a fixed cost
        ai, bi, r2i = fit([x["nodes"] for x in rows], [x["time_ms"] for x in rows])
        rounds.append({"round": r + 1, "rows": rows,
                       "intercept_ms_at_0_nodes": round(ai, 2),
                       "ms_per_million_nodes": round(bi * 1e6, 2),
                       "r2_time_vs_nodes": round(r2i, 5)})
        print("round %d: intercept %+.2f ms, %.2f ms per M-node, r2 %.5f"
              % (r + 1, ai, bi * 1e6, r2i))
        for x in rows:
            print("   depth %-2d nodes %-9d time %-5d nps %d" % (x["depth"], x["nodes"],
                                                                 x["time_ms"], x["nps"]))

    out = {"exe": exe, "settings": a.settings, "threads": 1,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "depths": depths, "rounds": rounds}
    with open(os.path.join(a.outdir, "check_29f3_%s.json" % a.settings), "w") as f:
        json.dump(out, f, indent=2)

    ic = [r["intercept_ms_at_0_nodes"] for r in rounds]
    print("\nfixed cost estimate (intercept at zero nodes): %s" % ic)
    if all(abs(x) < 1.0 for x in ic):
        print("verdict: NO measurable fixed cost inside the bench timer (<1 ms) -> 29-F3 NOT confirmed here")
    else:
        print("verdict: a nonzero intercept of about %.1f ms -> consistent with 29-F3's fixed cost"
              % (sum(ic) / len(ic)))


if __name__ == "__main__":
    main()
