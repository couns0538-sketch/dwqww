#!/usr/bin/env python3
"""guard_duty.py - how much of the wall time the GPU guard lets the npt trainer run, from F:\forge_nnue_train\gpu_guard.log.

Read-only. Stdlib only. Run: C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B guard_duty.py [opts]

The guard (tools\gpu_guard.ps1, owner's) writes one "ok" line per 10 minutes:
  <ts> ok hot=H memj=M src=hwinfo|adlx win10m(max hot=.. memj=.. hard=N run_frac=F avg_thr=T) total(...) lvl=L r=R targets=PIDS
run_frac = share of the window the trainer was NOT suspended; avg_thr = mean throttle r (r = rest share of every
second); targets empty = no trainer alive. It also writes "throttle r=..", "HARD SUSPEND", "HARD RESUME", "EMERGENCY".

Output per day (or per hour with --hourly): ok windows, windows with a trainer, mean / min run_frac and mean avg_thr
over those windows, hard suspends, emergency lines, source counts (hwinfo / adlx / none), mean hot / memj, and the
hours without an npt trainer alive (no_trainer_h; the GPU may still be used by another job in those hours).
--keeper <tsv>: joins the keeper's 5-minute GPU utilisation (column util) to each guard window and prints the mean
ratio util / run_frac for windows with a trainer = how busy the GPU is while the trainer is allowed to run
(1.0 = GPU-bound while running; well below 1 = the trainer waits for something else, e.g. the loader).
--probe-csv <hwinfo csv> [--rows N]: applies the guard's row pattern (zero-padded day: ^\\d\\d\\.\\d\\d\\.\\d{4}) and the
keeper's (1-2 digits) to the last N data rows of the CSV and prints how many rows each one accepts.
Exit 0; 2 when the log has no ok line in the range.
"""
import argparse
import datetime as dt
import os
import re
import statistics
import sys

TS = "%Y-%m-%dT%H:%M:%S"
RE_OK = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) ok hot=(-?[\d.]+) memj=(-?[\d.]+) src=(\w+) win10m\(max hot=\S+ "
                   r"memj=\S+ hard=(\d+) run_frac=([\d.]+) avg_thr=([\d.]+)\).*targets=(\S*)")
RE_EMG = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) EMERGENCY")
GUARD_ROW = re.compile(r"^\d\d\.\d\d\.\d{4}")          # as in gpu_guard.ps1 Read-Row ($rows filter)
KEEPER_ROW = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}")   # as in forge_npt_keeper.ps1 (unpadded day / month)


def parse_guard(path, t0, t1):
    wins, emg = [], []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = RE_OK.match(line)
            if m:
                ts = dt.datetime.strptime(m.group(1), TS)
                if t0 <= ts <= t1:
                    wins.append({"ts": ts, "hot": float(m.group(2)), "memj": float(m.group(3)), "src": m.group(4),
                                 "hard": int(m.group(5)), "run_frac": float(m.group(6)), "thr": float(m.group(7)),
                                 "trainer": bool(m.group(8))})
                continue
            me = RE_EMG.match(line)
            if me:
                ts = dt.datetime.strptime(me.group(1), TS)
                if t0 <= ts <= t1:
                    emg.append(ts)
    return wins, emg


def parse_keeper(path):
    """npt_keeper_log.tsv -> list of (ts, util %)."""
    out = []
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        hdr = fh.readline().rstrip("\r\n").split("\t")
        try:
            it, iu = hdr.index("time_pc"), hdr.index("util")
        except ValueError:
            return out
        for line in fh:
            f = line.rstrip("\r\n").split("\t")
            if len(f) <= max(it, iu):
                continue
            try:
                out.append((dt.datetime.strptime(f[it], TS), float(f[iu])))
            except ValueError:
                continue
    out.sort()
    return out


def keeper_util_in(keeper, t0, t1):
    v = [u for (ts, u) in keeper if t0 < ts <= t1]
    return statistics.fmean(v) if v else None


def probe_csv(path, rows):
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        fh.seek(max(0, size - 400 * rows))
        tail = fh.read().decode("latin-1").splitlines()[1:]
    data = [r for r in tail if re.match(r"^\d", r)][-rows:]
    g = sum(1 for r in data if GUARD_ROW.match(r))
    k = sum(1 for r in data if KEEPER_ROW.match(r))
    print(f"probe {path}: last {len(data)} data rows; first field example {data[-1].split(',')[0] if data else '?'}")
    print(f"  guard pattern ^dd.dd.yyyy accepts {g} / {len(data)}; keeper pattern ^d{{1,2}}.d{{1,2}}.yyyy accepts {k} / {len(data)}")
    if data and g == 0 and k == len(data):
        print("  -> the guard cannot read this file today (unpadded day or month); it falls back to its next feed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--guard", default="F:/forge_nnue_train/gpu_guard.log")
    ap.add_argument("--from", dest="t0", default="", help="YYYY-MM-DD[THH:MM] (default: 7 days before --to)")
    ap.add_argument("--to", dest="t1", default="", help="YYYY-MM-DD[THH:MM] (default: now)")
    ap.add_argument("--hourly", action="store_true")
    ap.add_argument("--keeper", default="", help="C:/Users/Administrator/grok-pc/forge_push/npt_keeper/npt_keeper_log.tsv")
    ap.add_argument("--probe-csv", default="", help="HWiNFO csv to test against the guard's row pattern (tail only)")
    ap.add_argument("--rows", type=int, default=50)
    a = ap.parse_args()

    def pt(s, default):
        if not s:
            return default
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M") if "T" in s else dt.datetime.strptime(s, "%Y-%m-%d")

    t1 = pt(a.t1, dt.datetime.now())
    t0 = pt(a.t0, t1 - dt.timedelta(days=7))
    if a.probe_csv:
        probe_csv(a.probe_csv, a.rows)
    wins, emg = parse_guard(a.guard, t0, t1)
    if not wins:
        print(f"no ok line in {a.guard} between {t0} and {t1}", file=sys.stderr)
        return 2
    keeper = parse_keeper(a.keeper)
    key = (lambda w: w["ts"].strftime("%Y-%m-%d %H:00")) if a.hourly else (lambda w: w["ts"].strftime("%Y-%m-%d"))
    groups = {}
    for w in wins:
        groups.setdefault(key(w), []).append(w)
    hdr = ["period", "windows", "with_trainer", "run_frac_mean", "run_frac_min", "thr_mean", "hard", "emerg",
           "src_hwinfo", "src_adlx", "src_other", "hot_mean", "memj_mean", "no_trainer_h"]
    if keeper:
        hdr += ["util_mean", "util_over_run_frac"]
    print("\t".join(hdr))
    for k in sorted(groups):
        g = groups[k]
        tr = [w for w in g if w["trainer"]]
        rf = [w["run_frac"] for w in tr]
        th = [w["thr"] for w in tr]
        ne = sum(1 for e in emg if key({"ts": e}) == k)
        row = [k, str(len(g)), str(len(tr)), f"{statistics.fmean(rf):.3f}" if rf else "", f"{min(rf):.3f}" if rf else "",
               f"{statistics.fmean(th):.3f}" if th else "", str(sum(w["hard"] for w in g)), str(ne),
               str(sum(1 for w in g if w["src"] == "hwinfo")), str(sum(1 for w in g if w["src"] == "adlx")),
               str(sum(1 for w in g if w["src"] not in ("hwinfo", "adlx"))),
               f"{statistics.fmean(w['hot'] for w in g):.0f}", f"{statistics.fmean(w['memj'] for w in g):.0f}",
               f"{sum(1 for w in g if not w['trainer']) / 6.0:.1f}"]
        if keeper:
            us, ratios = [], []
            for w in tr:
                u = keeper_util_in(keeper, w["ts"] - dt.timedelta(minutes=10), w["ts"])
                if u is not None:
                    us.append(u)
                    if w["run_frac"] > 0.05:
                        ratios.append(u / 100.0 / w["run_frac"])
            row += [f"{statistics.fmean(us):.1f}" if us else "", f"{statistics.fmean(ratios):.2f}" if ratios else ""]
        print("\t".join(row))
    return 0


if __name__ == "__main__":
    sys.exit(main())
