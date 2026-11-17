"""Clear cost as a function of Hash -- the number the memset implies, measured.

`TranspositionTable::clear()` is a full memset of the table (search.cpp:372-375), so the cost
of `ucinewgame` and `Clear Hash` should be linear in Hash and the SAME for both. The
H.32 run in soak3 gave p50 1.30 / 1.23 ms for a 32 MiB memset; this measures 64 / 256 / 1024
so the report quotes a measurement per size instead of an estimate derived from bandwidth.

200 calls per arm, enough for a median but not a benchmark.
"""
import json
import statistics
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402

fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:14]
out = []
for hash_mb in (32, 64, 256, 1024):
    row = {"hash": hash_mb}
    for mode in ("ucinewgame", "clearhash"):
        eng = Engine("/tmp/soak/build/forge", options={"Hash": hash_mb, "Threads": 1})
        eng.position_fen(fens[0])
        eng.go("go depth 8")
        rss0 = eng.rss_kb()
        times = []
        for _ in range(200):
            t = time.perf_counter()
            if mode == "ucinewgame":
                eng.newgame()
            else:
                eng.setoption("Clear Hash", "")
            times.append((time.perf_counter() - t) * 1000.0)
        rss1 = eng.rss_kb()
        eng.quit()
        times.sort()
        row[mode] = {"p50_ms": round(statistics.median(times), 3),
                     "p99_ms": round(times[int(len(times) * 0.99)], 3),
                     "min_ms": round(times[0], 3),
                     "rss_before": rss0, "rss_after": rss1}
    row["gb_per_s_clearhash"] = round(
        hash_mb / 1024.0 / (row["clearhash"]["p50_ms"] / 1000.0), 1)
    out.append(row)
    print(json.dumps(row))

json.dump(out, open("/tmp/soak/ev/soak3b_costs.json", "w"), indent=1)
