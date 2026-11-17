"""Measure the cost of seat 12's per-move scan, with wall-clock timing.

Q1 Is the scan entered on EVERY search or only on draw-adjudicated roots?
   -> counters (roots vs scanned_roots), probe build.
Q2 What does it cost, and is it visible? -> wall time on the SAME position and depth
   for base, patched, and the instrumented probe; plus probe scan_ns.

Every FEN is asserted with python-chess, and `go perft 1` is compared with python-chess's
legal-move count so a silently refused position cannot be mistaken for a measured one.
`go` is read to `bestmove` (never piping `quit` early, which makes the engine fabricate one).
"""
import json
import os
import re
import statistics
import subprocess
import sys

import chess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ucih import Engine, EngineError  # noqa: E402

PROBE = os.path.expanduser("~/b_probe/forge")
BASE = os.path.expanduser("~/b_base/forge")
PATCHED = os.path.expanduser("~/b_patched/forge")

NORMAL = [
    ("startpos", chess.STARTING_FEN),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("pos3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("mid1", "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"),
    ("mid2", "rnbqkb1r/pp2pppp/3p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"),
]

DRAWN = [
    ("A2_two_mates_h100", "8/8/8/8/8/8/1R2R3/K1k5 w - - 100 1"),
    ("C_stalemate_h100", "8/8/8/8/8/8/Q7/K1k5 w - - 100 1"),
    ("D_checknotmate_h100", "8/8/8/8/8/8/R7/K1k5 w - - 100 1"),
    ("E_mate_in_2_h100", "8/8/8/8/2R5/k7/8/1K6 w - - 100 1"),
    ("wide_h100", "8/8/4k3/8/3Q4/8/4K3/8 w - - 100 1"),
    ("wide42_h100", "8/8/3k4/8/2Q1B3/8/3K4/8 w - - 100 1"),
]


def validate(groups):
    rows = []
    for kind, group in groups:
        for name, fen in group:
            b = chess.Board(fen)
            assert b.is_valid(), "%s: ILLEGAL FEN %r" % (name, fen)
            assert b.fen() == fen, "%s: not canonical" % name
            rows.append({"name": name, "fen": fen, "kind": kind,
                         "py_legal": b.legal_moves.count()})
    return rows


def perft1(exe, fen):
    e = Engine(exe)
    try:
        e.send("ucinewgame")
        e.position(fen)
        _, n = e.perft(1, timeout=120.0)
        return n
    finally:
        e.quit()


def timed_search(exe, fen, depth, reps=5):
    """Wall time from sending `go` to reading `bestmove`, best of `reps`, plus nodes."""
    times = []
    nodes = 0
    bm = None
    maxd = 0
    for _ in range(reps):
        e = Engine(exe)
        try:
            e.send("ucinewgame")
            e.position(fen)
            import time
            t0 = time.monotonic()
            _, bm, info = e.go("go depth %d" % depth, timeout=600.0)
            times.append((time.monotonic() - t0) * 1000.0)
            nodes = e.nodes_from(info)
            maxd = max([int(l.split()[2]) for l in info if l.startswith("info depth")] or [0])
        finally:
            e.quit()
    return {"wall_ms_min": min(times), "wall_ms_median": statistics.median(times),
            "nodes": nodes, "bestmove": bm, "max_depth": maxd}


def probe_counters(fen, depth):
    env = dict(os.environ, SCANPROBE="1")
    script = "uci\nisready\nucinewgame\nisready\nposition fen %s\nisready\ngo depth %d\nquit\n" % (fen, depth)
    p = subprocess.run([PROBE], input=script, capture_output=True, text=True, env=env, timeout=600)
    if "invalid FEN" in p.stdout or "invalid FEN" in p.stderr:
        raise RuntimeError("refused %r" % fen)
    best = {}
    for line in p.stderr.splitlines():
        if line.startswith("SCANPROBE"):
            kv = {k: int(v) for k, v in re.findall(r"(\w+)=(\d+)", line)}
            if kv.get("roots", 0) >= 1:
                best = kv
    return best


def main():
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    rows = validate([("normal", NORMAL), ("drawn", DRAWN)])

    print("== position-identity gate (perft1 vs python-chess) ==")
    for r in rows:
        p1 = perft1(PROBE, r["fen"])
        r["perft1"] = p1
        assert p1 == r["py_legal"], "%s: perft1=%s py=%s" % (r["name"], p1, r["py_legal"])
        print("  %-20s perft1=%-4d py_legal=%-4d OK" % (r["name"], p1, r["py_legal"]))

    print("\n== counters: is the scan paid on every search? (probe, depth %d) ==" % depth)
    print("%-20s %-8s %6s %6s %8s %9s %12s" %
          ("position", "kind", "legal", "roots", "scanned", "iters", "scan_ns"))
    for r in rows:
        c = probe_counters(r["fen"], depth)
        r.update({"roots": c.get("roots", 0), "scanned_roots": c.get("scanned_roots", 0),
                  "iters": c.get("scan_iterations", 0), "scan_ns": c.get("scan_ns", 0)})
        print("%-20s %-8s %6d %6d %8d %9d %12d" % (
            r["name"], r["kind"], r["py_legal"], r["roots"], r["scanned_roots"],
            r["iters"], r["scan_ns"]))

    print("\n== wall time, base vs patched, depth %d, best of %d ==" % (depth, reps))
    print("%-20s %12s %12s %8s %10s %10s" %
          ("position", "base_ms", "patched_ms", "ratio", "nodes_b", "nodes_p"))
    for r in rows:
        rb = timed_search(BASE, r["fen"], depth, reps)
        rp = timed_search(PATCHED, r["fen"], depth, reps)
        r.update({"base": rb, "patched": rp})
        ratio = rp["wall_ms_min"] / rb["wall_ms_min"] if rb["wall_ms_min"] else float("nan")
        r["ratio"] = ratio
        print("%-20s %12.2f %12.2f %8.2f %10d %10d" % (
            r["name"], rb["wall_ms_min"], rp["wall_ms_min"], ratio,
            rb["nodes"], rp["nodes"]))

    with open(os.path.join(HERE, "scan_cost.json"), "w") as fh:
        json.dump({"depth": depth, "reps": reps, "rows": rows}, fh, indent=2)

    norm = [r for r in rows if r["kind"] == "normal"]
    drawn = [r for r in rows if r["kind"] == "drawn"]
    print("\n== summary ==")
    print("normal searches: %d, paid the scan: %d" % (len(norm), sum(1 for r in norm if r["scanned_roots"] > 0)))
    print("drawn  searches: %d, paid the scan: %d" % (len(drawn), sum(1 for r in drawn if r["scanned_roots"] > 0)))
    ratios = [r["ratio"] for r in norm]
    print("normal-root timing ratio patched/base: median %.3f, max %.3f" %
          (statistics.median(ratios), max(ratios)))


if __name__ == "__main__":
    main()
