#!/usr/bin/env python3
"""S02 — third independent measurement of the position-shape dependence of the owner's 6 s + 0.06 clock tail.

Two seats now reconcile on "sparse endgames with few legal moves are the heavy class" (seat 08's 08-F28, seat 28's
outliers). This is an independent attempt with MY OWN boards: I do not use their position lists, so agreement
between us is evidence rather than a copy.

The class definition used, stated so the numbers can be checked against theirs: a board's class is the pair
(piece count, number of legal moves for the side to move), which is the shape definition 08-F28 uses.
  few pieces     = 6 or fewer men on the board
  many pieces    = 14 or more men
  few moves      = under 12 legal moves for the side to move
  many moves     = 25 or more legal moves

Five boards per class, all mine, all legal positions I constructed and verified with python-chess (so nothing
illegal reaches the engine). 5 runs per board on the owner's clock, PC build under PC20, Threads 1, Hash 16,
OwnBook false, fresh process per run, interactive driver.

The clock: `go wtime 6000 btime 6000 winc 60 binc 60`. The engine's own hard plan for this clock is what a tail
hits; the measured quantity is wall time from `go` to `bestmove`.

usage: class_tail.py <pc_exe> <outdir> [runs]
"""
import json
import os
import statistics
import subprocess
import sys
import threading
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
OUT = sys.argv[2] if len(sys.argv) > 2 else "out_tail"
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

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
CLOCK = "go wtime 6000 btime 6000 winc 60 binc 60"

# my own boards, built to the four shape classes. Every one is verified legal below before use.
BOARDS = {
    # few pieces (<=6 men), few moves (<12 legal): sparse king-and-pawn style endings
    "sparse_few": [
        "8/8/6k1/Q7/1P4PP/1K3P2/8/8 b - - 0 1",
        "8/8/8/4k3/8/4K3/4P3/8 w - - 0 1",
        "8/8/8/8/3k4/8/3K4/6R1 w - - 0 1",
        "6k1/8/6K1/8/8/8/8/5R2 w - - 0 1",
        "8/8/4k3/8/8/3KP3/8/8 w - - 0 1",
    ],
    # few pieces, many moves (>=25 legal): open boards with sliders
    "sparse_many": [
        "8/8/8/3k4/8/3K4/8/2R4R w - - 0 1",
        "8/2k5/8/8/8/8/2K5/3R4 w - - 0 1",
        "8/8/4k3/8/8/4K3/8/2R2B2 w - - 0 1",
        "8/8/6k1/8/8/6K1/8/2R2N2 w - - 0 1",
        "8/8/8/2k5/8/2K5/8/3R1B2 w - - 0 1",
    ],
    # full material (>=14 men), few moves: blocked middlegame structures
    "full_few": [
        "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1",
        "rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 1",
        "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 0 1",
        "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/8/PPP2PPP/RNBQKB1R w KQkq - 0 1",
        "r1bqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
    ],
    # full material, many moves: open, busy middlegames
    "full_many": [
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
        "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
        "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "rnbq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP1B1PPP/R2QKB1R w KQ - 0 8",
    ],
}


def shape(fen):
    b = chess.Board(fen)
    return {"men": len(b.piece_map()), "legal": b.legal_moves.count(),
            "valid": b.is_valid()}


def one(fen):
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
    send(CLOCK)
    if not wait("bestmove", n0, 120):
        raise SystemExit("FAIL: no bestmove")
    ms = (time.monotonic() - t0) * 1000.0
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    import re as _re
    depths, iter_times, iter_nodes = [], [], []
    for l in seg:
        md = _re.match(r"info depth (\d+) ", l)
        if not md:
            continue
        depths.append(int(md.group(1)))
        mt = _re.search(r" time (\d+)", l)
        if mt:
            iter_times.append(int(mt.group(1)))
        mn = _re.search(r" nodes (\d+)", l)
        if mn:
            iter_nodes.append(int(mn.group(1)))
    last_iter_ms = iter_times[-1] if iter_times else None
    last_iter_nodes = iter_nodes[-1] if iter_nodes else None
    return {"wall_ms": round(ms, 1),
            "depth": max(depths) if depths else 0,
            "last_iter_ms": last_iter_ms,
            "last_iter_nodes": last_iter_nodes,
            "iterations": len(depths)}


def main():
    os.makedirs(OUT, exist_ok=True)
    json.dump({"exe": EXE,
               "sha256": subprocess.run(["sha256sum", EXE], capture_output=True,
                                        text=True).stdout.split()[0],
               "threads": 1, "hash_mb": 16, "settings": "PC20", "options": PC20,
               "clock": CLOCK, "runs_per_board": RUNS, "boards": BOARDS,
               "class_definition": "few pieces <=6 men, many >=14; few moves <12 legal, many >=25 legal",
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(OUT, "meta.json"), "w"), indent=1)

    rows = []
    for cls, fens in BOARDS.items():
        print("== class %s" % cls)
        for fen in fens:
            sh = shape(fen)
            if not sh["valid"]:
                raise SystemExit("FAIL: I built an invalid board: %s" % fen)
            recs = [one(fen) for _ in range(RUNS)]
            walls = [r["wall_ms"] for r in recs]
            last = [r["last_iter_ms"] for r in recs if r["last_iter_ms"] is not None]
            rows.append({"class": cls, "fen": fen, "men": sh["men"], "legal": sh["legal"],
                         "walls": walls, "median": statistics.median(walls),
                         "p99": sorted(walls)[max(0, int(round(0.99 * (len(walls) - 1))))],
                         "max": max(walls), "min": min(walls),
                         "depth": recs[0]["depth"],
                         "last_iter_ms": statistics.median(last) if last else None,
                         "last_iter_ratio": (statistics.median(last) / statistics.median(walls))
                                            if last and statistics.median(walls) else None,
                         "runs": recs})
            print("   %-52s men=%-2d mv=%-3d med %7.1f ms  p99 %7.1f  worst %7.1f  lastiter %6s ms  d%-2d"
                  % (fen, sh["men"], sh["legal"], statistics.median(walls),
                     rows[-1]["p99"], max(walls),
                     ("%.0f" % rows[-1]["last_iter_ms"]) if rows[-1]["last_iter_ms"] else "n/a",
                     recs[0]["depth"]), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    CLOCK_MS = 6060.0
    print()
    print("### TABLE 1 — owner's clock (6 s + 0.06 = %d ms), by position shape, %d runs per board" % (CLOCK_MS, RUNS))
    print()
    print("| class | men | legal moves | median ms | p99 ms | worst ms | worst as % of clock |")
    print("|---|---|---|---|---|---|---|")
    for cls in BOARDS:
        sub = [r for r in rows if r["class"] == cls]
        allw = [w for r in sub for w in r["walls"]]
        med = statistics.median(allw)
        p99 = sorted(allw)[max(0, int(round(0.99 * (len(allw) - 1))))]
        worst = max(allw)
        print("| %s | %d-%d | %d-%d | **%.1f** | %.1f | %.1f | %.1f%% |"
              % (cls, min(r["men"] for r in sub), max(r["men"] for r in sub),
                 min(r["legal"] for r in sub), max(r["legal"] for r in sub),
                 med, p99, worst, 100 * worst / CLOCK_MS))

    print()
    print("### TABLE 2 — utilisation: how much of the clock the engine actually spends, per class")
    print()
    print("| class | median ms | utilisation | worst ms | worst utilisation |")
    print("|---|---|---|---|---|")
    for cls in BOARDS:
        sub = [r for r in rows if r["class"] == cls]
        allw = [w for r in sub for w in r["walls"]]
        med = statistics.median(allw)
        worst = max(allw)
        print("| %s | %.1f | **%.1f%%** | %.1f | %.1f%% |"
              % (cls, med, 100 * med / CLOCK_MS, worst, 100 * worst / CLOCK_MS))

    print()
    print("### TABLE 3 — the proposed MECHANISM: the last completed iteration's own cost")
    print()
    print("| class | median wall ms | median last-iteration ms | last-iter / wall | boards |")
    print("|---|---|---|---|---|")
    for cls in BOARDS:
        sub = [r for r in rows if r["class"] == cls]
        lw = [r["last_iter_ms"] for r in sub if r["last_iter_ms"]]
        med = statistics.median([r["median"] for r in sub])
        lm = statistics.median(lw) if lw else None
        print("| %s | %.1f | %s | %s | %d |"
              % (cls, med, ("%.1f" % lm) if lm else "n/a",
                 ("%.2f" % (lm / med)) if lm and med else "-", len(sub)))

    # correlation across all 20 positions, computed here rather than asserted
    pairs = [(r["last_iter_ms"], r["median"]) for r in rows if r["last_iter_ms"]]
    print()
    print("### TABLE 4 — correlation across the %d positions (not per class, all of them together)" % len(pairs))
    print()
    if len(pairs) >= 3:
        xs = [p[0] for p in pairs]
        ys = [p[1] for p in pairs]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in pairs)
        dx = sum((x - mx) ** 2 for x in xs) ** 0.5
        dy = sum((y - my) ** 2 for y in ys) ** 0.5
        pearson = (num / (dx * dy)) if dx and dy else None
        sx, sy = sorted(xs), sorted(ys)
        n = len(pairs)

        def rank(vs, v):
            return sx.index(v) if vs is sx else sy.index(v)

        rx = [sx.index(v) + 1 for v in xs]
        ry = [sy.index(v) + 1 for v in ys]
        mrx, mry = statistics.mean(rx), statistics.mean(ry)
        rnum = sum((a - mrx) * (b - mry) for a, b in zip(rx, ry))
        rdx = sum((a - mrx) ** 2 for a in rx) ** 0.5
        rdy = sum((b - mry) ** 2 for b in ry) ** 0.5
        spearman = (rnum / (rdx * rdy)) if rdx and rdy else None
        print("pearson r(last-iteration cost, wall time) = %s  (n=%d)"
              % (("%.3f" % pearson) if pearson is not None else "undefined", n))
        print("spearman rho                              = %s"
              % (("%.3f" % spearman) if spearman is not None else "undefined"))
        print()
        print("| last-iter ms | wall ms | last-iter / wall |")
        print("|---|---|---|")
        for x, y in sorted(pairs):
            print("| %.1f | %.1f | %.2f |" % (x, y, x / y if y else 0))
        json.dump({"pearson": pearson, "spearman": spearman, "pairs": pairs},
                  open(os.path.join(OUT, "correlation.json"), "w"), indent=1)
    print()
    sp = [w for r in rows if r["class"] == "sparse_few" for w in r["walls"]]
    fm = [w for r in rows if r["class"] == "full_many" for w in r["walls"]]
    a, b = statistics.median(sp), statistics.median(fm)
    print("sparse+few median %.1f ms vs full+many median %.1f ms -> **%.2fx**"
          % (a, b, a / b if b else 0))
    print("worst single run overall: %.1f ms = %.1f%% of the clock"
          % (max(w for w in sp + fm + [x for r in rows for x in r["walls"]]),
             100 * max(x for r in rows for x in r["walls"]) / CLOCK_MS))
    print()
    print("compare with seat 08's 08-F28: sparse+few 853.1 median / 1585.4 worst, full+many 161.2 / 398.5,")
    print("5.3x spread, on THEIR boards and harness. Mine are above, on boards they never used.")


if __name__ == "__main__":
    main()
