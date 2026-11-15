#!/usr/bin/env python3
"""Job 8 step 1 controls, using the held-open driver."""
import json
import statistics
import sys
import time

sys.path.insert(0, '/tmp/ds')
from j8engine import Engine  # noqa: E402


def stopwatch(rounds=200):
    e = Engine()
    times = []
    for _ in range(rounds):
        t0 = time.monotonic()
        e.send("isready")
        e.until("readyok", 30)
        times.append((time.monotonic() - t0) * 1000.0)
    e.close()
    return times


def main():
    positions = json.load(open(sys.argv[1]))
    out_path = sys.argv[2]
    times = stopwatch(200)
    watch = {"rounds": len(times), "median_ms": round(statistics.median(times), 3),
             "max_ms": round(max(times), 3), "min_ms": round(min(times), 3),
             "p95_ms": round(sorted(times)[int(0.95 * len(times))], 3)}

    first_hits = sum(1 for p in positions if p["first_generated"] in p["mating_moves"])

    e = Engine()
    d2_hits = 0
    misses = []
    for p in positions:
        e.send("ucinewgame")
        mv, infos, ms, to = e.go(f"position fen {p['fen']}", "depth 2", timeout=20)
        if mv in p["mating_moves"]:
            d2_hits += 1
        elif len(misses) < 10:
            misses.append({"fen": p["fen"], "best": mv, "mating": p["mating_moves"],
                           "info_lines": len(infos)})
    e.close()
    out = {"stopwatch": watch,
           "first_legal_move_player": {"hits": first_hits, "of": len(positions)},
           "depth2_player": {"hits": d2_hits, "of": len(positions), "misses": misses}}
    json.dump(out, open(out_path, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "depth2_player"}, indent=1))
    print(f"depth 2: {d2_hits}/{len(positions)}")


if __name__ == "__main__":
    main()
