#!/usr/bin/env python3
"""S02 — is the MultiPV node-budget dilution PROPORTIONAL to MultiPV, or worse?

`go nodes 20000`, MultiPV 1 / 2 / 4 / 8, one position, measuring per cell:
  * the PRIMARY line's own node cost and the depth it reached,
  * the TOTAL nodes spent across all lines.
If the primary line gets ~1/M of the budget, dilution is proportional and the rule is simply "do not combine a
fixed budget with MultiPV above 1". If it gets WORSE than 1/M, the extra lines cost more than their share and
that is a second finding.

How the primary line's cost is read: the engine emits one `info depth D multipv K ... nodes N` line per line at
each depth, where `nodes` is CUMULATIVE for that line within the iteration. So at the final depth, the multipv 1
line's `nodes` value is the primary line's own cost for that iteration, and the multipv M line's value is the
total for the whole iteration. Both are read straight off the engine's output, not inferred.

PC r15 build, PC20, Threads 1, Hash 16, OwnBook false, fresh process, interactive driver, COLD.

usage: dilution.py <pc_exe> <outdir> [runs]
"""
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_dil"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

PC20 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
N = 20000
MPVS = [1, 2, 4, 8]


def run(multipv):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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

    def wait(pref, n0=0, to=180.0):
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
        raise SystemExit("FAIL: no uciok")
    for s in PC20:
        send(s)
    send("setoption name MultiPV value %d" % multipv)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + FEN)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    t0 = time.monotonic()
    send("go nodes %d" % N)
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove")
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    # Group by DEPTH, then by multipv, keeping every line (not just the last per index).
    by_depth = {}
    for line in seg:
        m = re.match(r"info depth (\d+) multipv (\d+) score (\S+) (-?\d+) seldepth (\d+) nodes (\d+) ", line)
        if m:
            d, k = int(m.group(1)), int(m.group(2))
            by_depth.setdefault(d, {})[k] = (int(m.group(6)), int(m.group(4)))
            continue
        # MultiPV 1: the engine emits no `multipv` field. Format:
        #   info depth D seldepth S score cp V nodes N nps ... hashfull ... time ... pv ...
        m2 = re.match(r"info depth (\d+) seldepth (\d+) score (\S+) (-?\d+) nodes (\d+) ", line)
        if m2:
            d = int(m2.group(1))
            by_depth.setdefault(d, {})[1] = (int(m2.group(5)), int(m2.group(4)))
    depths_seen = set(by_depth)
    final_depth = max(depths_seen) if depths_seen else 0
    at_final = by_depth.get(final_depth, {})
    # multipv 1's `nodes` is its own cumulative cost; the LAST line of the iteration carries the total.
    primary_nodes = at_final.get(1, (None, None))[0]
    total_nodes = None
    if at_final:
        last_key = max(at_final)
        total_nodes = at_final[last_key][0]
        # multi-line searches: the M-th line's `nodes` is cumulative for the whole iteration
        if last_key > 1:
            total_nodes = at_final[last_key][0]
    return {"ms": round(ms, 0), "final_depth": final_depth,
            "primary_nodes": primary_nodes, "total_nodes": total_nodes,
            "lines_at_final": len(at_final),
            "all_lines": {str(k): v for k, v in sorted(at_final.items())}}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "position": FEN, "go": "go nodes %d" % N, "multipvs": MPVS, "runs": RUNS,
               "how_read": "the engine's own `info depth D multipv K ... nodes V` lines; V is cumulative for "
                           "line K in that iteration, so at the final depth multipv 1's V is the primary "
                           "line's own cost and the largest V is the whole iteration's total",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    res = {}
    for m in MPVS:
        rs = [run(m) for _ in range(RUNS)]
        det = len({(r["final_depth"], r["primary_nodes"], r["total_nodes"]) for r in rs}) == 1
        r0 = rs[0]
        res[m] = {"runs": RUNS, "deterministic": det,
                  "depth": r0["final_depth"], "primary_nodes": r0["primary_nodes"],
                  "total_nodes": r0["total_nodes"], "lines": r0["lines_at_final"],
                  "ms": statistics.median([r["ms"] for r in rs]),
                  "all_lines": r0["all_lines"]}
        print("  MultiPV %d -> depth %d, primary line %s nodes, total %s nodes, %d lines, %.0f ms  det=%s"
              % (m, r0["final_depth"], r0["primary_nodes"], r0["total_nodes"],
                 r0["lines_at_final"], res[m]["ms"], det), flush=True)

    base = res[1]
    print()
    print("### dilution, measured on one position, `go nodes %d`" % N)
    print()
    print("| MultiPV | lines | depth | primary line nodes | share of N | total nodes | total / N | depth loss |")
    print("|---|---|---|---|---|---|---|---|")
    for m in MPVS:
        r = res[m]
        share = (r["primary_nodes"] / N) if r["primary_nodes"] else None
        total_ratio = (r["total_nodes"] / N) if r["total_nodes"] else None
        print("| %d | %d | %d | %s | %s | %s | %s | %d |"
              % (m, r["lines"], r["depth"], r["primary_nodes"],
                 ("%.3f (%.1f%% of 1/M=%.3f)" % (share, 100 * share, 1.0 / m)) if share else "-",
                 r["total_nodes"], ("%.2f" % total_ratio) if total_ratio else "-",
                 base["depth"] - r["depth"]))

    print()
    print("### is the primary line's share ~1/M, or worse?")
    print()
    print("| MultiPV | M | primary share of N | 1/M | share / (1/M) | reading |")
    print("|---|---|---|---|---|---|")
    for m in MPVS:
        if m == 1:
            continue
        r = res[m]
        if not r["primary_nodes"]:
            continue
        share = r["primary_nodes"] / N
        ideal = 1.0 / m
        ratio = share / ideal
        reading = ("proportional or better" if ratio >= 0.9
                   else ("WORSE than 1/M" if ratio < 0.75 else "slightly worse than 1/M"))
        print("| %d | %d | %.4f | %.4f | %.2f | %s |" % (m, m, share, ideal, ratio, reading))

    json.dump(res, open(os.path.join(OUT, "dilution.json"), "w"), indent=1)
    print()
    print("raw: dilution.json, meta.json")


if __name__ == "__main__":
    main()
