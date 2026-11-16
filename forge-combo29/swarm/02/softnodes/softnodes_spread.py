#!/usr/bin/env python3
"""S02 — resolve a CONFLICT: seat 13's softnodes overshoot (up to 164%) vs my S-F8 (max 2.06x = 106%).

Their claim: "worst observed 409,130 nodes past a 250,000 budget (164 %; 659,130 nodes total) on a real game
position, so a match budgeting 250,000 nodes can spend more than twice that on one move."

My S-F8 measured N in {2000, 20000, 50000, 250000} on startpos, a middlegame and an endgame, and found
nodes/N between 1.08 and 2.06 with the hard cap at 4N never exceeded. Those two CAN both be true if the spread
depends on the position: my worst case was 2.06x at N=2000, theirs 2.64x at N=250000 on a game position.

So this measures the overshoot distribution on a WIDER set than either of us used, including positions from real
games where the depth cost per iteration varies most, at N=250000 (their case) AND at the other budgets, and
reports the full distribution rather than my previous max.

Reading the source first, so the test checks a stated model: the soft budget stops at the end of the first
iteration that passes N (src/search.cpp:2932) and the hard cap is 4N (src/search.cpp:2498-2501), so the model
predicts nodes >= N, nodes <= 4N, and an overshoot bounded by one iteration's cost.

PC r15, PC20, Threads 1, Hash 16, OwnBook false, fresh process per run (a softnodes stop point is a NODE count,
so seat 10's cold rule applies), interactive driver, COLD.

usage: softnodes_spread.py <pc_exe> <outdir>
"""
import json
import os
import statistics
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_spread"

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

# real-game style positions, deliberately varied in tactical density (iterations cost wildly different amounts)
POSITIONS = {
    "g_mid_sharp": "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
    "g_mid_quiet": "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "g_mid_tactical": "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "g_kiwipete": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "g_end_rook": "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "g_end_sparse": "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1",
    "g_start": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
}
NS = [2000, 20000, 50000, 250000]
CAP_RATIO = 4.0


def one(fen, n):
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
    send("go softnodes %d" % n)
    if not wait("bestmove", n0, 240):
        raise SystemExit("FAIL: no bestmove for softnodes %d" % n)
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    # the engine's own reported total for the search
    reported = None
    for line in seg:
        if "softnodes nodes" in line:
            try:
                reported = int(line.split("softnodes nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
    last_info = None
    for line in seg:
        if line.startswith("info depth"):
            last_info = line
    nodes = reported
    if nodes is None and last_info:
        import re
        m = re.search(r" nodes (\d+)", last_info)
        if m:
            nodes = int(m.group(1))
    depth = None
    if last_info:
        import re
        m = re.match(r"info depth (\d+)", last_info)
        if m:
            depth = int(m.group(1))
    return {"nodes": nodes, "depth": depth, "reported": reported}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "positions": POSITIONS, "ns": NS,
               "model": "soft stop at the end of the first iteration passing N (search.cpp:2932); "
                        "hard cap 4N (search.cpp:2498-2501)",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    rows = []
    print("== softnodes overshoot, 7 positions x 4 budgets, PC20, Threads 1")
    for name, fen in POSITIONS.items():
        for n in NS:
            r = one(fen, n)
            if r["nodes"] is None:
                print("   %-16s N=%-7d NO NODE COUNT" % (name, n))
                continue
            over = r["nodes"] - n
            pct = 100.0 * over / n
            rows.append({"position": name, "n": n, "nodes": r["nodes"], "depth": r["depth"],
                         "overshoot": over, "pct": round(pct, 1),
                         "ratio": round(r["nodes"] / n, 3),
                         "within_cap": r["nodes"] <= CAP_RATIO * n})
            print("   %-16s N=%-7d -> %-8d nodes  (+%5.1f%%)  ratio %.2f  d%s  cap=%s"
                  % (name, n, r["nodes"], pct, r["nodes"] / n, r["depth"],
                     "ok" if r["nodes"] <= CAP_RATIO * n else "**EXCEEDED**"), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    print()
    print("### distribution of nodes/N over %d cells" % len(rows))
    ratios = sorted(r["ratio"] for r in rows)
    if ratios:
        print("| statistic | value |")
        print("|---|---|")
        print("| min | %.2f |" % ratios[0])
        print("| median | %.2f |" % statistics.median(ratios))
        print("| p90 | %.2f |" % ratios[min(len(ratios) - 1, int(0.9 * (len(ratios) - 1)))])
        print("| max | %.2f |" % ratios[-1])
        print("| cells over the 4N hard cap | %d of %d |"
              % (sum(1 for r in rows if not r["within_cap"]), len(rows)))
        worst = max(rows, key=lambda r: r["ratio"])
        print("| worst cell | %s at N=%d, %d nodes (+%.0f%%) |"
              % (worst["position"], worst["n"], worst["nodes"], worst["pct"]))
    print()
    if any(not r["within_cap"] for r in rows):
        print("**The 4N hard cap WAS exceeded — that is a defect and it contradicts my S-F8's model reading.**")
    else:
        print("**The 4N hard cap held in every cell**, so seat 13's 164%% and my 106%% are both inside the")
        print("model; they differ only in which position/budget they sampled, not in the rule.")
    print()
    print("raw: rows.json, meta.json")


if __name__ == "__main__":
    main()
