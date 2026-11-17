"""Soak 4: 1,000 MultiPV-4 searches at Hash 64, one process.

Why this is the expensive path (source, on this base commit):
  search.cpp:2384-2390  the alternate table is built ONCE per top-level search, with
                        hash_mb recomputed from the main table's cluster count, so at
                        Hash 64 it is another 64 MB.
  search.cpp:2502       `alt_shared->tt.clear()` runs before EVERY secondary line, i.e.
                        three 64 MiB memsets per depth iteration for MultiPV 4.
  search.cpp:2388-2390  the alternate SharedSearchState is a unique_ptr owned by the search
                        frame, so it dies at the end of the search -- unless something
                        retains it.

The measurement therefore samples RSS twice per search: the in-search peak (sampler thread,
2 ms) and the value after `bestmove`. A retained table shows as a rising `after` column; a
cache that fills shows as a rising `peak` with a flat `after`; a clean per-search temporary
shows as a peak that returns to the same `after` every time.
"""
import argparse
import json
import sys
import threading
import time

sys.path.insert(0, "/tmp/soak/tools")
from uci import Engine  # noqa: E402


class Sampler(threading.Thread):
    def __init__(self, eng, period=0.002):
        super().__init__(daemon=True)
        self.eng = eng
        self.period = period
        self.peak = 0
        self.active = False
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.peak = 0

    def run(self):
        while True:
            with self.lock:
                active = self.active
            if active:
                try:
                    r = self.eng.rss_kb()
                    if r:
                        with self.lock:
                            self.peak = max(self.peak, r)
                except Exception:
                    pass
            time.sleep(self.period)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--searches", type=int, default=1000)
    ap.add_argument("--hash", type=int, default=64)
    ap.add_argument("--multipv", type=int, default=4)
    ap.add_argument("--depth", type=int, default=9)
    ap.add_argument("--sample-every", type=int, default=25)
    args = ap.parse_args()

    fens = [l.strip() for l in open("/tmp/soak/positions_R.fens") if l.strip()][10:70]
    eng = Engine(args.exe, options={"Hash": args.hash, "Threads": 1,
                                    "MultiPV": args.multipv})
    sampler = Sampler(eng)
    sampler.start()
    settled = eng.rss_kb()
    t0 = time.monotonic()
    cum = 0
    csv_path = args.out + ".csv"
    log_path = args.out + ".log"
    with open(csv_path, "w") as csv, open(log_path, "w") as log:
        csv.write("search,peak_kb,after_kb,elapsed_s,cum_nodes\n")
        csv.write("0,%d,%d,0.0,0\n" % (settled, settled))
        log.write(json.dumps({"event": "start", "settled": settled,
                              "options": eng.sent, "id": eng.id_name}) + "\n")
        for i in range(1, args.searches + 1):
            fen = fens[(i - 1) % len(fens)]
            eng.position_fen(fen)
            sampler.reset()
            sampler.active = True
            r = eng.go("go depth %d" % args.depth)
            sampler.active = False
            time.sleep(0.004)
            with sampler.lock:
                peak = sampler.peak
            after = eng.rss_kb()
            cum += r["nodes"] or 0
            log.write(json.dumps({"search": i, "nodes": r["nodes"],
                                  "best": r["bestmove"]}) + "\n")
            if i % args.sample_every == 0 or i <= 5:
                csv.write("%d,%d,%d,%.2f,%d\n"
                          % (i, peak, after, time.monotonic() - t0, cum))
                csv.flush()
            if not eng.alive():
                log.write(json.dumps({"search": i, "ERROR": "died",
                                      "rc": eng.proc.returncode}) + "\n")
                break
    final = eng.rss_kb()
    eng.quit()
    print(json.dumps({"searches": args.searches, "settled": settled, "final": final,
                      "delta_kb": final - settled,
                      "elapsed_s": round(time.monotonic() - t0, 1)}))


if __name__ == "__main__":
    main()
