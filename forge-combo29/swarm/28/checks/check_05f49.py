#!/usr/bin/env python3
"""check_05f49.py EXE OUTDIR — seat 28's independent check of seat 05's S-F49 control ranking.

Claim restated from seat 05's sentence alone: the owner's real controls rank by depth
    softnodes 2000 < nodes 20000 < nodes 50000 < nodes 250000 < clock 6s+0.06 < movetime 6000
and the clock row reaches depth ~18 at 300k-780k nodes, beating the 250k node budget.

My own boards, my own harness: PC r15 + PC20, Threads 1, Hash 16, OwnBook false.
H6/H7 test seat 05's own contention caveat: the clock row solo vs under a deliberate parallel load.

Usage: check_05f49.py EXE OUTDIR
"""
import multiprocessing
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# My own boards — NOT seat 05's. A quiet deep middlegame, a normal opening, and a second middlegame.
BOARDS = [
    ("deep middlegame", "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8"),
    ("opening", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("second middlegame", "r2q1rk1/pp1bbppp/2np1n2/2p1p3/2P1P3/2NP1N2/PP1BBPPP/R2Q1RK1 w - - 0 9"),
]

CONTROLS = [
    ("softnodes 2000", "go softnodes 2000"),
    ("nodes 20000", "go nodes 20000"),
    ("nodes 50000", "go nodes 50000"),
    ("nodes 250000", "go nodes 250000"),
    ("clock 6+0.06", "go wtime 6000 btime 6000 winc 60 binc 60"),
    ("movetime 6000", "go movetime 6000"),
]


def run_one(exe, fen, cmd):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("Threads", 1), ("Hash", 16)] + list(S14.items()) + PC20_EXTRA:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    eng.send("ucinewgame")
    eng.send("isready")
    eng.read_until("readyok", 20)
    eng.send(f"position fen {fen}")
    eng.send("isready")
    eng.read_until("readyok", 20)
    t0 = time.monotonic()
    eng.send(cmd)
    out, ok = eng.read_until("bestmove", 120)
    t1 = time.monotonic()
    eng.close()
    depth, nodes, best = 0, 0, ""
    for line in out:
        if line.startswith("bestmove"):
            p = line.split()
            best = p[1] if len(p) > 1 else ""
        if line.startswith("info depth"):
            f = line.split()
            depth = max(depth, int(f[f.index("depth") + 1]))
            if "nodes" in f:
                nodes = int(f[f.index("nodes") + 1])
    return {"depth": depth, "nodes": nodes, "best": best,
            "wall": (t1 - t0) * 1000.0, "ok": ok}


def burner(stop_flag):
    """Busy loop to create CPU contention on the other cores."""
    x = 0
    while not stop_flag.value:
        x = (x * 1103515245 + 12345) & 0xFFFFFFFF


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    print(f"PC r15 + PC20, Threads 1, Hash 16, OwnBook false; {len(BOARDS)} boards of my own")
    print()
    print("| board | control | depth | nodes | wall ms | bestmove |")
    print("|---|---|---|---|---|---|")
    results = {}
    for bname, fen in BOARDS:
        for cname, cmd in CONTROLS:
            r = run_one(exe, fen, cmd)
            results[(bname, cname)] = r
            print(f"| {bname} | {cname} | {r['depth']} | {r['nodes']} | {r['wall']:.0f} | "
                  f"{r['best']} |", flush=True)
        print("|---|---|---|---|---|---|")

    print()
    print("## The ranking test (H1-H3): is the depth order monotone across controls?")
    print()
    print("| board | softnodes 2k | nodes 20k | nodes 50k | nodes 250k | clock 6+.06 | movetime 6s | order monotone? |")
    print("|---|---|---|---|---|---|---|---|")
    order_ok = []
    for bname, _fen in BOARDS:
        vals = [results[(bname, c[0])]["depth"] for c in CONTROLS]
        mono = all(a <= b for a, b in zip(vals, vals[1:]))
        order_ok.append(mono)
        print(f"| {bname} | " + " | ".join(str(v) for v in vals) + f" | {'YES' if mono else '**NO**'} |")

    print()
    print("## The contention caveat (H6-H7): the clock row solo vs under a deliberate load")
    print()
    print("| condition | board | depth | nodes | wall ms | bestmove |")
    print("|---|---|---|---|---|---|")
    fen = BOARDS[0][1]
    solo = [run_one(exe, fen, "go wtime 6000 btime 6000 winc 60 binc 60") for _ in range(3)]
    for i, r in enumerate(solo, 1):
        print(f"| solo run {i} | {BOARDS[0][0]} | {r['depth']} | {r['nodes']} | {r['wall']:.0f} | {r['best']} |")

    stop_flag = multiprocessing.Value('b', False)
    procs = [multiprocessing.Process(target=burner, args=(stop_flag,))
             for _ in range(max(1, (os.cpu_count() or 2) - 1))]
    for p in procs:
        p.start()
    time.sleep(0.5)
    try:
        loaded = [run_one(exe, fen, "go wtime 6000 btime 6000 winc 60 binc 60") for _ in range(3)]
        for i, r in enumerate(loaded, 1):
            print(f"| under load {i} | {BOARDS[0][0]} | {r['depth']} | {r['nodes']} | {r['wall']:.0f} | {r['best']} |")
    finally:
        stop_flag.value = True
        for p in procs:
            p.join(timeout=3)
            if p.is_alive():
                p.terminate()

    solo_nodes = {r["nodes"] for r in solo}
    load_nodes = {r["nodes"] for r in loaded}
    print()
    print(f"solo node counts: {sorted(solo_nodes)}")
    print(f"loaded node counts: {sorted(load_nodes)}")
    print(f"clock row reproducible SOLO (same nodes all 3): {len(solo_nodes) == 1}")
    print(f"clock row CHANGED under load: {load_nodes != solo_nodes}")
    with open(os.path.join(outdir, "check_05f49.tsv"), "w") as fh:
        fh.write("board\tcontrol\tdepth\tnodes\twall_ms\tbestmove\n")
        for (bname, cname), r in results.items():
            fh.write(f"{bname}\t{cname}\t{r['depth']}\t{r['nodes']}\t{r['wall']:.0f}\t{r['best']}\n")
        for i, r in enumerate(solo, 1):
            fh.write(f"solo{i}\tclock\t{r['depth']}\t{r['nodes']}\t{r['wall']:.0f}\t{r['best']}\n")
        for i, r in enumerate(loaded, 1):
            fh.write(f"loaded{i}\tclock\t{r['depth']}\t{r['nodes']}\t{r['wall']:.0f}\t{r['best']}\n")
    return 0 if all(order_ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
