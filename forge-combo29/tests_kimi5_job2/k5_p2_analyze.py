#!/usr/bin/env python3
"""kimi5 job2 Part 2 analysis: OFF vs one ON json, per clock line.
Prints per clock: n, engine-time median/mean/p95/max (ms) for both, time factor ON/OFF
(median of per-search ratios and ratio of medians), mean depth drop, bestmove-diff rate,
share of ON searches with >=1 hold/adjust line."""
import json
import statistics
import sys


def load(path):
    d = json.load(open(path))
    recs = {}
    for r in d["records"]:
        if r.get("failed") or r.get("timeout"):
            continue
        recs[(r["pos"], r["clock"])] = r
    return d, recs


def pct(vals, q):
    s = sorted(vals)
    if not s:
        return None
    k = max(0, min(len(s) - 1, int(round((q / 100.0) * (len(s) - 1)))))
    return s[k]


def main():
    off_path, on_path = sys.argv[1], sys.argv[2]
    off_d, off = load(off_path)
    on_d, on = load(on_path)
    clocks = off_d["clocks"]
    print(f"ON label={on_d['label']} setopt={on_d['setopt']}")
    print(f"{'clock':>13} {'n':>4} {'tMed':>6} {'tMean':>7} {'tP95':>6} {'tMax':>6} "
          f"{'facMed':>7} {'facRat':>7} {'dDepth':>7} {'bmDiff':>7} {'sig%':>6}")
    rows = []
    for ci, (t, inc) in enumerate(clocks):
        pairs = [(off[(p, ci)], on[(p, ci)])
                 for p in range(off_d["n_positions"])
                 if (p, ci) in off and (p, ci) in on]
        n = len(pairs)
        if n == 0:
            continue
        ot = [o["engine_time"] for o, _ in pairs if o["engine_time"] is not None]
        nt = [w["engine_time"] for _, w in pairs if w["engine_time"] is not None]
        ratios = [w["engine_time"] / o["engine_time"] for o, w in pairs
                  if o["engine_time"] and w["engine_time"] and o["engine_time"] > 0]
        ddepth = statistics.mean(w["depth"] - o["depth"] for o, w in pairs
                                 if o["depth"] is not None and w["depth"] is not None)
        bmdiff = sum(1 for o, w in pairs if o["bestmove"] != w["bestmove"]) / n
        sig = sum(1 for _, w in pairs if w["holds"] > 0 or w["adjusts"] > 0) / n
        row = {"clock": f"{t}+{inc}", "n": n,
               "off_med": statistics.median(ot), "off_mean": statistics.mean(ot),
               "off_p95": pct(ot, 95), "off_max": max(ot),
               "on_med": statistics.median(nt), "on_mean": statistics.mean(nt),
               "on_p95": pct(nt, 95), "on_max": max(nt),
               "fac_med": statistics.median(ratios) if ratios else None,
               "fac_rat": statistics.median(nt) / statistics.median(ot),
               "ddepth": ddepth, "bmdiff": bmdiff, "sig": sig}
        rows.append(row)
        print(f"{t:>7}+{inc:<5} {n:>4} {row['on_med']:>6.0f} {row['on_mean']:>7.1f} "
              f"{row['on_p95']:>6.0f} {row['on_max']:>6.0f} "
              f"{row['fac_med']:>7.3f} {row['fac_rat']:>7.3f} {ddepth:>7.2f} "
              f"{bmdiff:>7.3f} {sig:>6.2f}")
    json.dump(rows, open(sys.argv[3], "w"), indent=1)


if __name__ == "__main__":
    main()
