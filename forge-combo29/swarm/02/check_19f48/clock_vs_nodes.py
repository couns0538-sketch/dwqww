#!/usr/bin/env python3
"""S02 — does the divergence exist between the owner's CLOCK mode (`go movetime`) and the NODE mode?

Nobody has compared the clock against `go nodes`/`go softnodes` on ambiguous positions. The owner's match path is
`go nodes` and the strength path is the clock, so if these two also diverge on near-equal moves then mixing them
across a season's data is as unsafe as mixing the two node commands — which is a practical finding for the owner,
not a curiosity.

The hard part is making the comparison FAIR: `go nodes N` and `go movetime T` are different limits, so "the same
effort" has to be established rather than assumed. I do it in two steps:
  1. calibrate: on a neutral position, measure the wall time of `go nodes 50000` and the nodes of `go movetime` at
     a few times, to pick a movetime that lands in the same node/time region;
  2. compare: on ambiguous positions, run `go nodes 50000` and `go movetime <calibrated>` and compare bestmoves,
     reporting each run's own node count so the reader can see how close the efforts really were.

I report the effort mismatch honestly rather than pretending the modes were equalised: a divergence at genuinely
different effort proves less than one at matched effort.

PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process per search, interactive driver, COLD.

usage: clock_vs_nodes.py <pc_exe> <outdir>
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
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_cvn"

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
# the same ambiguous positions S-C10 used, so the three modes are compared on identical boards
AMBIGUOUS = [
    ("gap2", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8"),
    ("gap5", "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1"),
    ("gap5b", "2rq1rk1/pp1bppbp/2np1np1/8/3NP3/1BN1BP2/PPPQ2PP/2KR3R w - - 0 11"),
    ("gap9", "r2qk2r/ppp1bppp/2n1bn2/3p4/3P4/2N1BN2/PPPB1PPP/R2QKB1R w KQkq - 0 8"),
    ("gap13", "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 7"),
    ("gap15", "r1bq1rk1/pp3ppp/2nbpn2/3p4/3P4/2NBPN2/PP3PPP/R1BQ1RK1 w - - 0 9"),
]
CALIBRATION_BOARD = "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9"
NODE_BUDGET = 50000
MOVETIMES = [50, 100, 200]


def run(fen, go):
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
            time.sleep(0.0005)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok")
    for s in PC20:
        send(s)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + fen)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    t0 = time.monotonic()
    send(go)
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove for %r" % go)
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    nodes = None
    depth = None
    for line in seg:
        if line.startswith("info depth"):
            m = re.search(r" nodes (\d+)", line)
            if m:
                nodes = int(m.group(1))
            md = re.match(r"info depth (\d+)", line)
            if md:
                depth = int(md.group(1))
    return {"bestmove": bm[-1].split()[1] if bm else None,
            "nodes": nodes, "depth": depth, "wall_ms": round(ms, 1)}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "ambiguous": AMBIGUOUS, "node_budget": NODE_BUDGET,
               "movetimes_checked": MOVETIMES, "calibration_board": CALIBRATION_BOARD,
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    print("== step 1: calibrate a movetime against `go nodes %d` on a neutral board" % NODE_BUDGET)
    nb = [run(CALIBRATION_BOARD, "go nodes %d" % NODE_BUDGET) for _ in range(2)]
    print("   `go nodes %d`      -> %s" % (NODE_BUDGET, [(r["nodes"], r["wall_ms"]) for r in nb]))
    calib = {}
    for mt in MOVETIMES:
        rs = [run(CALIBRATION_BOARD, "go movetime %d" % mt) for _ in range(2)]
        calib[mt] = rs
        print("   `go movetime %-4d` -> %s" % (mt, [(r["nodes"], r["wall_ms"]) for r in rs]))
    # pick the movetime whose node count is CLOSEST to the node budget's
    target = statistics.median([r["nodes"] for r in nb if r["nodes"]])
    best_mt = min(MOVETIMES, key=lambda mt: abs(statistics.median(
        [r["nodes"] for r in calib[mt] if r["nodes"]]) - target))
    chosen_nodes = statistics.median([r["nodes"] for r in calib[best_mt] if r["nodes"]])
    print()
    print("   node budget reaches %d nodes -> closest movetime is %d ms, which reaches %d nodes (ratio %.2f)"
          % (target, best_mt, chosen_nodes, chosen_nodes / target))
    print()

    print("== step 2: the two modes on the ambiguous positions")
    print()
    print("| position | gap | `go nodes %d` | nodes | depth | `go movetime %d` | nodes | depth | agree |"
          % (NODE_BUDGET, best_mt))
    print("|---|---|---|---|---|---|---|---|---|")
    rows = []
    differ = 0
    for gap, fen in AMBIGUOUS:
        a = run(fen, "go nodes %d" % NODE_BUDGET)
        b = run(fen, "go movetime %d" % best_mt)
        d = (a["bestmove"] != b["bestmove"])
        differ += d
        rows.append({"gap": gap, "fen": fen, "nodes_mode": a, "clock_mode": b, "differ": d})
        print("| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
              % (gap, gap, a["bestmove"], a["nodes"], a["depth"],
                 b["bestmove"], b["nodes"], b["depth"],
                 "**DIFFER**" if d else "agree"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    print("### verdict")
    print("- positions compared: %d" % len(rows))
    print("- differing bestmoves: **%d of %d**" % (differ, len(rows)))
    nratio = statistics.median([r["clock_mode"]["nodes"] / r["nodes_mode"]["nodes"]
                                for r in rows if r["clock_mode"]["nodes"] and r["nodes_mode"]["nodes"]])
    print("- median clock-mode nodes / node-mode nodes: **%.2f**" % nratio)
    print()
    if differ:
        print("CONCLUSION: the CLOCK mode and the NODE mode also diverge on ambiguous positions, so the owner's")
        print("            strength path and match path are not comparable move-for-move either.")
    else:
        print("CONCLUSION: no divergence seen between the clock and node modes on these ambiguous positions.")


if __name__ == "__main__":
    main()
