#!/usr/bin/env python3
"""S02 — `go softnodes N` on the PC build under PC20, Threads 1: the new area FABLE_TO_swarm_6 suggests.

File 6 names the owner's self-play path as `go softnodes 2000` and asks three questions:
  1. is it DETERMINISTIC run to run (file 6 says it must be)?
  2. does it stop at a FINISHED depth?
  3. how far past N does it go?

The semantics I read in the source first (include/forge/search.hpp:31-33, src/search.cpp:2497-2502 and
src/search.cpp:2932), so the measurement tests a stated model rather than a guess:
  * the SOFT budget is a finished-iteration target: after each completed iteration, if nodes >= N, stop
    (src/search.cpp:2932, "The iteration above is finished. Passing the soft budget stops here, keeping this
    move and score.");
  * the HARD budget is 4 x N, kept on the normal node stop, so a runaway iteration is still cut and its partial
    move discarded (src/search.cpp:2498-2501).
So the model predicts: nodes >= N always, nodes <= 4N always, and the stop is at an iteration boundary.

Method: Threads 1, Hash 16, OwnBook false, full PC20, fresh process per run, interactive driver. For each N in
{2000, 20000, 50000, 250000} (the values file 6 names, plus the two it does not test) and each of several
positions: 3 runs, comparing the whole emitted output (scores, depths, nodes, bestmove) for determinism.

A softnodes search's stop point is a NODE count, and file 6/seat 10 both matter here: node counts are only
comparable COLD, which every run here is (first search of a fresh process).

usage: softnodes_probe.py <pc_exe> <outdir> [runs]
"""
import json
import os
import re
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_soft"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3

PC20 = [
    "setoption name Threads value 1",
    "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true",
    "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true",
    "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true",
    "setoption name OwnBook value false",
]
POSITIONS = {
    "startpos": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "middlegame": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "endgame": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
}
NS = [2000, 20000, 50000, 250000]


def run(fen, n):
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

    def wait(pref, n0=0, to=120.0):
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
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok under PC20")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: PC20 option refused: %r" % line)
    send("position fen " + fen)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    t0 = time.monotonic()
    send("go softnodes %d" % n)
    if not wait("bestmove", n0, 180):
        raise SystemExit("FAIL: no bestmove for softnodes %d" % n)
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    depths = []
    nodes_seen = []
    for line in seg:
        m = re.match(r"info depth (\d+) .* nodes (\d+) ", line)
        if m:
            depths.append(int(m.group(1)))
            nodes_seen.append(int(m.group(2)))
    sm = [l for l in seg if "softnodes nodes" in l]
    soft_reported = None
    if sm:
        mm = re.search(r"softnodes nodes (\d+)", sm[-1])
        if mm:
            soft_reported = int(mm.group(1))
    bm = [l for l in seg if l.startswith("bestmove")]
    # the lines that define "the same output", timing fields excluded
    norm = [re.sub(r"(time|nps) \d+", r"\1 <X>", l) for l in seg if l.startswith("info depth")]
    return {"ms": round(ms, 0),
            "final_depth": max(depths) if depths else 0,
            "last_nodes": nodes_seen[-1] if nodes_seen else None,
            "soft_reported_nodes": soft_reported,
            "bestmove": bm[-1].split()[1] if bm else None,
            "norm": norm,
            "distinct_depths": sorted(set(depths))}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "settings": "PC20", "options": PC20,
               "positions": POSITIONS, "ns": NS, "runs": RUNS,
               "model_read_from_source": "soft budget stops after a FINISHED iteration when nodes >= N "
                                         "(search.cpp:2932); hard cap 4xN on the normal node stop "
                                         "(search.cpp:2498-2501)",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    rows = []
    print("== 3 questions: deterministic? finished depth? how far past N?")
    for pos_name, fen in POSITIONS.items():
        for n in NS:
            runs = [run(fen, n) for _ in range(RUNS)]
            deterministic = all(r["norm"] == runs[0]["norm"] for r in runs)
            bm_same = all(r["bestmove"] == runs[0]["bestmove"] for r in runs)
            last = runs[0]["last_nodes"]
            ratio = (last / n) if last else None
            row = {"position": pos_name, "n": n,
                   "deterministic": deterministic, "bestmove_same": bm_same,
                   "final_depth": [r["final_depth"] for r in runs],
                   "last_nodes": [r["last_nodes"] for r in runs],
                   "soft_reported": [r["soft_reported_nodes"] for r in runs],
                   "bestmove": runs[0]["bestmove"],
                   "ms": [r["ms"] for r in runs],
                   "nodes_over_n": round(ratio, 3) if ratio else None}
            rows.append(row)
            print("  %-10s N=%-6d det=%-5s bm=%-5s depth=%-10s nodes=%-16s (x%.2f of N)  reported=%s  %sms"
                  % (pos_name, n, deterministic, bm_same,
                     row["final_depth"], row["last_nodes"],
                     ratio or 0, row["soft_reported"], row["ms"][0]), flush=True)

    print()
    print("### TABLE — `go softnodes N`, PC20, Threads 1, %d runs per cell" % RUNS)
    print()
    print("| position | N | deterministic | depth | nodes at stop | nodes / N | >= N? | <= 4N? | bestmove |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        ln = r["last_nodes"][0]
        print("| %s | %d | %s | %d | %d | %.2f | %s | %s | %s |"
              % (r["position"], r["n"], "YES" if r["deterministic"] else "**NO**",
                 r["final_depth"][0], ln, r["nodes_over_n"] or 0,
                 "yes" if ln >= r["n"] else "**NO**",
                 "yes" if ln <= 4 * r["n"] else "**NO**",
                 r["bestmove"]))
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    det_all = all(r["deterministic"] for r in rows)
    ge = all(r["last_nodes"][0] >= r["n"] for r in rows)
    le = all(r["last_nodes"][0] <= 4 * r["n"] for r in rows)
    print("### verdict against the source model")
    print("- deterministic across %d runs in every cell: %s" % (RUNS, "PASS" if det_all else "FAIL"))
    print("- nodes at stop >= N in every cell:              %s" % ("PASS" if ge else "FAIL"))
    print("- nodes at stop <= 4N in every cell:             %s" % ("PASS" if le else "FAIL"))
    over = [r for r in rows if r["nodes_over_n"] and r["nodes_over_n"] > 2.0]
    print("- cells where the overshoot exceeds 2x N:        %d of %d" % (len(over), len(rows)))
    for r in over:
        print("    %s N=%d -> %.2fx" % (r["position"], r["n"], r["nodes_over_n"]))


if __name__ == "__main__":
    main()
