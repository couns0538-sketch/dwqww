#!/usr/bin/env python3
"""gpu_util_stats.py - Opus R14-B: how busy was the GPU? Read-only statistics from the keeper's HWiNFO log (own code).

usage: python -I -B gpu_util_stats.py [--csv PATH] [--hours 6 | --from "YYYY-MM-DD HH:MM" [--to "YYYY-MM-DD HH:MM"]]
                                      [--by-hour] [--min-samples 10]
Default CSV: the file the crew's npt keeper reads (C:/Users/Administrator/grok-pc/nnue/tools/hwinfo/gpu_sensors.csv,
HWiNFO, one row every ~2 s, written live). The window is found by binary search on the file's timestamps, so only that
part is read (the file is ~260 MB); a half-written last row is skipped. Columns: GPU Utilization [%] (the keeper's
"GPU util"), GPU Computing (Compute 0) Usage [%], GPU Memory Controller Utilization [%], GPU PPT (Sustained) [W].
Per column: samples, mean, p10 / p50 / p90, min, max; for utilisation also the share of samples >= 90 % (item 1's
target) and <= 10 % (GPU waiting). --by-hour adds hourly means of GPU Utilization. Exit 0, or 2 when the window holds
fewer than --min-samples rows. Never writes anything.
"""
import argparse
import datetime as dt
import os
import statistics
import sys

DEFAULT_CSV = "C:/Users/Administrator/grok-pc/nnue/tools/hwinfo/gpu_sensors.csv"
COLUMNS = ["GPU Utilization [%]", "GPU Computing (Compute 0) Usage [%]", "GPU Memory Controller Utilization [%]",
           "GPU PPT (Sustained) [W]"]


def parse_time(line):
    """'2.11.2026,21:12:38.015,...' -> datetime (HWiNFO writes d.m.yyyy and unpadded H:M:S), None if not a data row."""
    try:
        d, t = line.split(",", 2)[:2]
        day, month, year = (int(x) for x in d.split("."))
        h, m, s = t.split(":")
        sec = float(s)
        return dt.datetime(year, month, day, int(h), int(m), int(sec), int((sec % 1) * 1e6))
    except (ValueError, IndexError):
        return None


def first_offset_at_or_after(fh, size, when):
    """Byte offset of the first data row with time >= when (rows are in time order)."""
    lo, hi = 0, size
    while hi - lo > 65536:
        mid = (lo + hi) // 2
        fh.seek(mid)
        fh.readline()  # skip to the next row start
        t = None
        while t is None:
            line = fh.readline()
            if not line:
                break
            t = parse_time(line.decode("latin-1"))
        if t is None or t >= when:
            hi = mid
        else:
            lo = mid
    return lo


def pct(sorted_vals, q):
    return sorted_vals[min(len(sorted_vals) - 1, int(q * len(sorted_vals)))]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--hours", type=float, default=6.0)
    ap.add_argument("--from", dest="start")
    ap.add_argument("--to", dest="end")
    ap.add_argument("--by-hour", action="store_true")
    ap.add_argument("--min-samples", type=int, default=10)
    a = ap.parse_args()
    size = os.path.getsize(a.csv)
    with open(a.csv, "rb") as fh:
        header = [h.strip().strip('"') for h in fh.readline().decode("latin-1").rstrip("\r\n").split(",")]
        idx = {c: header.index(c) for c in COLUMNS if c in header}
        if COLUMNS[0] not in idx:
            print(f"gpu_util_stats: no '{COLUMNS[0]}' column in {a.csv}", file=sys.stderr)
            return 2
        fh.seek(max(0, size - 65536))
        tail = fh.read().decode("latin-1").splitlines()
        last = next((t for t in (parse_time(x) for x in reversed(tail)) if t), None)
        if last is None:
            print("gpu_util_stats: no data rows", file=sys.stderr)
            return 2
        try:
            end = dt.datetime.strptime(a.end, "%Y-%m-%d %H:%M") if a.end else last
            start = dt.datetime.strptime(a.start, "%Y-%m-%d %H:%M") if a.start else end - dt.timedelta(hours=a.hours)
        except ValueError:
            ap.error("--from / --to must be YYYY-MM-DD HH:MM")
        if start >= end:
            ap.error(f"the window is empty: --from {start:%Y-%m-%d %H:%M} is not before --to {end:%Y-%m-%d %H:%M}")
        fh.seek(0)
        fh.readline()
        first = next((t for t in (parse_time(fh.readline().decode("latin-1")) for _ in range(5)) if t), None)
        fh.seek(first_offset_at_or_after(fh, size, start))
        fh.readline()
        vals = {c: [] for c in idx}
        hourly = {}
        rows = 0
        for raw in fh:
            line = raw.decode("latin-1")
            t = parse_time(line)
            if t is None or t < start:
                continue
            if t > end:
                break
            f = line.rstrip("\r\n").split(",")
            # HWiNFO writes one value more than it names, at the end of the row (after "Total Errors"); the named
            # columns line up. A shorter row is one HWiNFO is still writing.
            if len(f) < len(header):
                continue
            rows += 1
            for c, i in idx.items():
                try:
                    vals[c].append(float(f[i]))
                except ValueError:
                    pass
            u = vals[COLUMNS[0]][-1] if vals[COLUMNS[0]] else None
            if u is not None:
                hourly.setdefault(t.strftime("%m-%d %H:00"), []).append(u)
    span = f"{first:%Y-%m-%d %H:%M:%S}" if first else "?"
    print(f"{a.csv}: {start:%Y-%m-%d %H:%M:%S} -> {end:%Y-%m-%d %H:%M:%S}, {rows} rows (the file covers {span} -> "
          f"{last:%Y-%m-%d %H:%M:%S})")
    if rows < a.min_samples:
        print(f"gpu_util_stats: only {rows} rows in the window", file=sys.stderr)
        return 2
    for c in COLUMNS:
        if c not in idx or not vals[c]:
            print(f"  {c}: not in the file")
            continue
        v = sorted(vals[c])
        line = (f"  {c}: n {len(v)}, mean {statistics.fmean(v):.1f}, p10 {pct(v, .1):.1f}, p50 {pct(v, .5):.1f}, "
                f"p90 {pct(v, .9):.1f}, min {v[0]:.1f}, max {v[-1]:.1f}")
        if c.endswith("[%]"):
            line += (f", >= 90 %: {100 * sum(x >= 90 for x in v) / len(v):.1f} % of samples, <= 10 %: "
                     f"{100 * sum(x <= 10 for x in v) / len(v):.1f} %")
        print(line)
    if a.by_hour:
        print("  hourly mean GPU Utilization [%]: " + ", ".join(
            f"{h[6:]} {statistics.fmean(u):.0f} ({len(u)})" for h, u in sorted(hourly.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
