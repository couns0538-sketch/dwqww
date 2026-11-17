"""Soak 3: repeated clearing. Does either clear leak, and does 5,000 clears leave RSS
where it started?

Two arms, identical protocol, same position sequence:
  ucinewgame   -> Searcher::clear()   = shared_.tt.clear() + every Worker::clear()
                                       (search.cpp:2678-2682). Worker::clear() resets the
                                       histories and the evaluator cache; the histories are
                                       real memory (~6.6 MB of ContinuationHistory at 13x64
                                       PieceToHistory) and are NOT reallocated.
  Clear Hash   -> Searcher::clear_hash() = shared_.tt.clear() + Worker::clear_caches()
                                       (search.cpp:2667-2671), i.e. the evaluator cache only.

Both call TranspositionTable::clear(), which is a full memset of the table
(search.cpp:372-375). At Hash 32 that is 5,000 x 32 MiB = 160 GB of writes for EITHER arm,
so the two arms are predicted to be similar in TIME as well as in RSS. Any large time
difference has to be attributed to the extra history/cache work, not to traffic that only
one of them does -- measured below as the per-call wall time of each.

RSS is sampled every 100 clears; a leak of even a few hundred bytes per call would be
visible across 5,000 calls, which is the point of the count.
"""
import argparse
import json
import statistics
import sys
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402


def run_arm(exe, mode, clears, hash_mb, out):
    fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:40]
    eng = Engine(exe, options={"Hash": hash_mb, "Threads": 1})
    for fen in fens:                      # warm the caches so the baseline is steady
        eng.position_fen(fen)
        eng.go("go depth 8")
    rss0 = eng.rss_kb()
    t0 = time.monotonic()
    rows = []
    per_call = []
    for i in range(1, clears + 1):
        c0 = time.perf_counter()
        if mode == "ucinewgame":
            eng.newgame()
        else:
            eng.setoption("Clear Hash", "")
        per_call.append((time.perf_counter() - c0) * 1000.0)
        if i % 100 == 0:
            rows.append({"clear": i, "rss_kb": eng.rss_kb(),
                         "elapsed_s": round(time.monotonic() - t0, 2)})
    # after the loop: does a search still give the same answer as a fresh process gives?
    rss1 = eng.rss_kb()
    eng.position_fen(fens[0])
    r = eng.go("go depth 10")
    eng.quit()
    per_call.sort()
    summary = {"mode": mode, "hash": hash_mb, "clears": clears,
               "rss_before": rss0, "rss_after": rss1,
               "delta_kb": rss1 - rss0,
               "elapsed_s": round(time.monotonic() - t0, 2),
               "ms_p50": round(statistics.median(per_call), 3),
               "ms_p99": round(per_call[int(len(per_call) * 0.99)], 3),
               "ms_total_sum": round(sum(per_call) / 1000.0, 2),
               "search_after_best": r["bestmove"], "search_after_nodes": r["nodes"]}
    with open("%s_%s.json" % (out, mode), "w") as f:
        json.dump({"summary": summary, "samples": rows}, f, indent=1)
    print(json.dumps(summary))
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--clears", type=int, default=5000)
    ap.add_argument("--hash", type=int, default=32)
    args = ap.parse_args()
    for mode in ("ucinewgame", "clearhash"):
        run_arm(args.exe, mode, args.clears, args.hash, args.out)


if __name__ == "__main__":
    main()
