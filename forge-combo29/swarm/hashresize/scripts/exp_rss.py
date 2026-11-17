"""Experiment D - RSS across repeated resizes (question 3).

A one-shot resize cannot show a leak: the process exits before the second
allocation.  This arm cycles 16 -> 256 -> 16 twenty times in ONE process and
reads /proc/<pid>/status after every transition.

The reading that matters is not "did RSS go up" but:

  * does RSS after `Hash 16` return to the same band on every cycle (freed), or
    climb monotonically (leaked)?
  * does `VmHWM` (the kernel's high-water mark) stop moving after the first
    large allocation, which is what a reused arena looks like?
  * does the process still produce the correct pinned answer at the end, so a
    "no leak" reading is not bought by a silently-corrupted engine?

Controls:
  * a process that only ever sets Hash 16 (no cycles) bounds the small-size RSS;
  * a process that only ever sets Hash 256 bounds the large-size RSS, so the
    expected step is known before the leak question is asked;
  * `go depth 16` after the cycles must answer the pinned startpos bench
    signature, proving the tables still work at the end.

RSS is sampled after an `isready` round-trip, so the setoption has been applied
(both are handled by the same command loop).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_client import Engine, ENGINE, proc_mem

PIN_FENS = [
    "rnbqkb1r/pp1pn1pp/2p5/3P4/2P1pp2/4B2N/PP2PPPP/RN1QKB1R w KQkq - 0 1",
]


def sample(e):
    e.sync()
    return proc_mem(e.p.pid)


def bounds(engine, hash_mb):
    """RSS a process settles at when it only ever sees one Hash value."""
    e = Engine(engine)
    try:
        e.handshake()
        base = sample(e)
        e.setoption("Hash", hash_mb)
        after = sample(e)
        return {"before": base, "after": after}
    finally:
        e.close()


def cycle(engine, small, large, rounds, search_between):
    e = Engine(engine)
    rec = {"rounds": []}
    try:
        e.handshake()
        e.setoption("Hash", small)
        e.setoption("Hash", large)
        e.setoption("Hash", small)
        t0 = time.perf_counter()
        for i in range(rounds):
            e.setoption("Hash", large)
            hi = sample(e)
            e.setoption("Hash", small)
            lo = sample(e)
            moved = {
                "round": i,
                "rss_after_large": hi.get("VmRSS"),
                "rss_after_small": lo.get("VmRSS"),
                "hwm_after_large": hi.get("VmHWM"),
                "hwm_after_small": lo.get("VmHWM"),
                "vsize_after_large": hi.get("VmSize"),
                "vsize_after_small": lo.get("VmSize"),
            }
            if search_between:
                r = e.search("position fen " + PIN_FENS[0], "go depth 12", timeout=120)
                moved["search_nodes"] = r["nodes"]
                moved["search_bestmove"] = r["bestmove"]
                moved["rss_after_search"] = proc_mem(e.p.pid).get("VmRSS")
            rec["rounds"].append(moved)
        rec["elapsed_s"] = round(time.perf_counter() - t0, 3)
        # engine still correct at the end?
        e.setoption("Hash", small)
        e.newgame()
        final = e.search("position startpos", "go depth 13", timeout=300)
        rec["final_startpos"] = {"nodes": final["nodes"], "bestmove": final["bestmove"]}
        e.send("bench 11")
        lines, _ = e.lines_until("info string bench", timeout=300)
        rec["final_bench11"] = [l for l in lines if "bench depth" in l]
        rec["end"] = proc_mem(e.p.pid)
    finally:
        e.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default=ENGINE)
    ap.add_argument("--small", type=int, default=16)
    ap.add_argument("--large", type=int, default=256)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--search-between", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = {
        "args": vars(args),
        "small_only": bounds(args.engine, args.small),
        "large_only": bounds(args.engine, args.large),
        "cycles_plain": cycle(args.engine, args.small, args.large, args.rounds, False),
        "cycles_with_search": cycle(args.engine, args.small, args.large, args.rounds, True),
    }
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)

    print("== one-size bounds (KB) ==")
    print("  small only  before RSS %s -> after RSS %s" % (
        out["small_only"]["before"].get("VmRSS"), out["small_only"]["after"].get("VmRSS")))
    print("  large only  before RSS %s -> after RSS %s" % (
        out["large_only"]["before"].get("VmRSS"), out["large_only"]["after"].get("VmRSS")))
    for name in ("cycles_plain", "cycles_with_search"):
        c = out[name]
        print("\n== %s: %d rounds, %.1fs ==" % (name, len(c["rounds"]), c["elapsed_s"]))
        print("  round  RSS@large  RSS@small   HWM@large  HWM@small  VSZ@small")
        for r in c["rounds"]:
            print("  %5d %10s %10s %11s %10s %10s" % (
                r["round"], r["rss_after_large"], r["rss_after_small"],
                r["hwm_after_large"], r["hwm_after_small"], r["vsize_after_small"]))
        print("  final startpos: %s" % c["final_startpos"])
        print("  final bench11 : %s" % c["final_bench11"])

    # leak arithmetic
    for name in ("cycles_plain", "cycles_with_search"):
        smalls = [r["rss_after_small"] for r in out[name]["rounds"] if r["rss_after_small"]]
        larges = [r["rss_after_large"] for r in out[name]["rounds"] if r["rss_after_large"]]
        if len(smalls) > 3:
            first, last = smalls[1], smalls[-1]
            print("\n%s: small RSS first=%d last=%d delta=%d KB; large first=%d last=%d delta=%d KB" % (
                name, first, last, last - first, larges[1], larges[-1], larges[-1] - larges[1]))


if __name__ == "__main__":
    main()
