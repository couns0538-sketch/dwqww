"""Soak 2: RSS as a function of `Hash`; the MultiPV alternate table's peak and release;
the resize transient (old + new held at once).

Three separate things, reported separately, because they are three different peaks:

  arm A  table residency      RSS after N searches at Hash 1/16/64/256/1024.
  arm R  resize transient     RSS peak during `setoption name Hash`, sampled every 2 ms.
                              `TranspositionTable::resize` (src/search.cpp:362-370) allocates
                              the new array before assigning over `clusters_`, so this peak
                              is old+new, NOT a search peak.
  arm B  MultiPV second table RSS peak *during* the search against RSS after `bestmove`,
                              sampled from a thread. `search.cpp:2384-2390` builds the
                              alternate table with `hash_mb` recomputed from the main
                              table's cluster count, so it is the same size as the main
                              table. The `after` column is what says whether it is freed.

A sample taken after `bestmove` cannot see a table that lives only for the search, so
arm B never uses one.
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
        self.samples = 0
        self.active = False
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.peak = 0
            self.samples = 0

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
                            self.samples += 1
                except Exception:
                    pass
            time.sleep(self.period)


def peak_of(fn, sampler):
    sampler.reset()
    sampler.active = True
    r = fn()
    sampler.active = False
    with sampler.lock:
        peak, n = sampler.peak, sampler.samples
    return peak, n, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--positions", default="/tmp/soak/positions_R.fens")
    ap.add_argument("--searches", type=int, default=40)
    args = ap.parse_args()

    fens = [l.strip() for l in open(args.positions) if l.strip()][10:70]
    out = []

    def emit(rec):
        out.append(rec)
        print(json.dumps({k: v for k, v in rec.items() if k != "per_search"}))

    # ---------- arm A: table residency ----------
    for h in (1, 16, 64, 256, 1024):
        eng = Engine(args.exe, options={"Hash": h, "Threads": 1})
        sampler = Sampler(eng)
        sampler.start()
        vm0 = eng.vm_kb()
        for fen in fens[:args.searches]:
            eng.position_fen(fen)
            eng.go("go depth 10")
        vm1 = eng.vm_kb()
        eng.quit()
        emit({"arm": "A", "hash": h, "rss_start": vm0["VmRSS"],
              "rss_after": vm1["VmRSS"], "vmpeak": vm1["VmPeak"],
              "vmsize": vm1["VmSize"],
              "rss_over_hash1": None})

    base = [r for r in out if r["arm"] == "A" and r["hash"] == 1][0]["rss_after"]
    for r in out:
        if r["arm"] == "A":
            r["rss_over_hash1"] = r["rss_after"] - base
    for r in out:
        if r["arm"] == "A":
            print("A hash=%4d rss=%7d vmpeak=%8d over_hash1=%8d"
                  % (r["hash"], r["rss_after"], r["vmpeak"], r["rss_over_hash1"]))

    # ---------- arm R: resize transient ----------
    for a, b in ((16, 256), (256, 256), (256, 16), (1024, 64)):
        eng = Engine(args.exe, options={"Hash": a, "Threads": 1})
        sampler = Sampler(eng)
        sampler.start()
        before = eng.rss_kb()
        peak, n, _ = peak_of(lambda: eng.setoption("Hash", b), sampler)
        time.sleep(0.02)
        after = eng.rss_kb()
        eng.quit()
        emit({"arm": "R", "from": a, "to": b, "rss_before": before,
              "peak_during": peak, "rss_after": after, "samples": n,
              "transient_mb": round((peak - max(a, b) * 1024) / 1024.0, 1)
              if peak else None})

    # ---------- arm B: MultiPV alternate table ----------
    for h, mpv, depth, npos in ((64, 1, 10, 10), (64, 4, 9, 6),
                                (256, 1, 10, 6), (256, 2, 9, 4),
                                (256, 4, 8, 3)):
        eng = Engine(args.exe, options={"Hash": h, "Threads": 1, "MultiPV": mpv})
        sampler = Sampler(eng)
        sampler.start()
        settled = eng.rss_kb()
        per = []
        for fen in fens[:npos]:
            eng.position_fen(fen)

            def do(fen=fen):
                return eng.go("go depth %d" % depth)

            peak, n, r = peak_of(do, sampler)
            time.sleep(0.01)
            after = eng.rss_kb()
            per.append({"peak": peak, "after": after, "samples": n,
                        "nodes": r["nodes"], "best": r["bestmove"]})
        eng.quit()
        peaks = [p["peak"] for p in per]
        afters = [p["after"] for p in per]
        rec = {"arm": "B", "hash": h, "multipv": mpv, "depth": depth,
               "rss_settled": settled,
               "peak_median": sorted(peaks)[len(peaks) // 2],
               "after_median": sorted(afters)[len(afters) // 2],
               "samples_min": min(p["samples"] for p in per),
               "per_search": per}
        emit(rec)
        print("B hash=%d mpv=%d depth=%d settled=%d peak_med=%d after_med=%d"
              % (h, mpv, depth, settled, rec["peak_median"], rec["after_median"]))

    with open(args.out + ".json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
