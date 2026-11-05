#!/usr/bin/env python3
"""npt_epochs.py - per-epoch wall time, it/s, restarts and waste of the live npt (nnue-pytorch) line, from logs only.

Read-only. Stdlib only. Run: C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B npt_epochs.py [opts]

Sources (never written):
  <runs-dir>/<run>.log, <run>.resume*.log   adapter logs: "[npt-adapter] <ts> try N:", "checkpoint epoch=E-step=S.ckpt",
                                            "SOFT GUARD", "child exit N", "guard exit 97: backing off N min"
  <runs-dir>/<run>/npt_try<k>.log           trainer stdout: "Epoch E (Train): 100%| a/b [mm:ss<..., X it/s",
                                            20/40/60/80 % marks, "[train_loss_epoch=.., unique=.., total=.., preskip=..]",
                                            "Epoch E (Val) : 100%| 61/61 [00:07<", "[guard] ABORT"
  --guard gpu_guard.log (optional)          "ok hot=.. win10m(... run_frac=F avg_thr=T ...) targets=.." every 10 min

Per epoch it prints: run, try, epoch, end time, wall minutes (ckpt to ckpt), train minutes (progress bar), it/s, kept
positions/s (batch 16384), the four segment rates between the 20 % marks (first vs last shows the read-ahead drain),
preskip ratio (records read per kept position), validation seconds, overhead seconds (wall - train - val), and with
--guard the mean run_frac of the guard windows inside the epoch and the derived "running it/s" = it/s / run_frac
(an ESTIMATE: it assumes the trainer makes no progress while suspended).
Per run it prints: tries, aborts (exit 97), epochs trained more than once, partial epochs lost at an abort, backoff
minutes, wall hours, and the share of wall time that produced a kept epoch.
Exit 0; 2 when no run matched.
"""
import argparse
import datetime as dt
import glob
import os
import re
import statistics
import sys

TS = "%Y-%m-%dT%H:%M:%S"
RE_AD = re.compile(r"^\[npt-adapter\] (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) (.*)$")
RE_CK = re.compile(r"checkpoint epoch=(\d+)-step=(\d+)\.ckpt")
RE_TRY = re.compile(r"^try (\d+):")
RE_EXIT = re.compile(r"^child exit (\d+)")
RE_BACK = re.compile(r"backing off (\d+) min")
RE_SOFT = re.compile(r"^SOFT GUARD: .*child suspended")
RE_MARK = re.compile(r"^Epoch\s+(\d+) \(Train\):\s+(\d+)%\|\s+(\d+)/(\d+)\s+\[(\d+:\d\d(?::\d\d)?)<[^,]*,\s+([\d.]+)it/s")
RE_STAT = re.compile(r"^Epoch\s+(\d+) \(Train\): \[train_loss_epoch=([\d.e-]+), unique=(\d+), total=(\d+), preskip=(\d+)\]")
RE_VAL = re.compile(r"^Epoch\s+(\d+) \(Val\)\s*:\s+100%\|\s+\d+/\d+\s+\[(\d+:\d\d(?::\d\d)?)<")
RE_VLOSS = re.compile(r"^Epoch\s+(\d+) \(Val\): \[val_loss_epoch=([\d.e-]+)\]")
RE_ABORT = re.compile(r"^\[guard\] ABORT")
RE_OK = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d) ok .*run_frac=([\d.]+) avg_thr=([\d.]+).*targets=(\S*)")


def hms(s):
    p = [int(x) for x in s.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]


def parse_adapter(path):
    """One adapter log -> list of tries: {n, start, cmd_ts, ckpts:[(ts, epoch, step)], exit, backoff, soft}."""
    tries = []
    cur = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = RE_AD.match(line.rstrip("\r\n"))
            if not m:
                continue
            ts = dt.datetime.strptime(m.group(1), TS)
            rest = m.group(2)
            mt = RE_TRY.match(rest)
            if mt:
                cur = {"n": int(mt.group(1)), "start": ts, "ckpts": [], "exit": None, "backoff": 0, "soft": 0,
                       "exit_ts": None, "resume": False}
                tries.append(cur)
                continue
            if cur is None:
                continue
            if rest.startswith("cmd:"):
                cur["resume"] = "--resume-from-checkpoint" in rest
                continue
            mc = RE_CK.search(rest)
            if mc:
                cur["ckpts"].append((ts, int(mc.group(1)), int(mc.group(2))))
                continue
            me = RE_EXIT.match(rest)
            if me:
                cur["exit"] = int(me.group(1))
                cur["exit_ts"] = ts
                continue
            mb = RE_BACK.search(rest)
            if mb:
                cur["backoff"] += int(mb.group(1))
                continue
            if RE_SOFT.match(rest):
                cur["soft"] += 1
    return tries


RE_VER = re.compile(r"^Using log dir .*version_(\d+)\s*$")


def parse_try_log(path):
    """One trainer stdout -> list of sessions (version, epochs, abort, last). The adapter appends a resume's attempt k
    to the same npt_try<k>.log, so a file can hold several sessions; each starts with "Using log dir ... version_K".
    epochs = {epoch: {marks:[(pct, steps, total, elapsed_s, its)], train_s, its, unique, total, preskip, val_s,
    val_loss}}; abort = the in-process guard aborted; last = (epoch, pct) of the last progress mark."""
    sessions = []
    ep = {}
    abort = False
    last = None
    ver = -1
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\r\n")
            mv0 = RE_VER.match(line)
            if mv0:
                if ep or abort:
                    sessions.append((ver, ep, abort, last))
                ep, abort, last, ver = {}, False, None, int(mv0.group(1))
                continue
            mm = RE_MARK.match(line)
            if mm:
                e = int(mm.group(1))
                d = ep.setdefault(e, {"marks": []})
                d["marks"].append((int(mm.group(2)), int(mm.group(3)), int(mm.group(4)), hms(mm.group(5)),
                                   float(mm.group(6))))
                if int(mm.group(2)) == 100:
                    d["train_s"] = hms(mm.group(5))
                    d["its"] = float(mm.group(6))
                    d["steps"] = int(mm.group(4))
                last = (e, int(mm.group(2)))
                continue
            ms = RE_STAT.match(line)
            if ms:
                d = ep.setdefault(int(ms.group(1)), {"marks": []})
                d["train_loss"] = float(ms.group(2))
                d["unique"], d["total"], d["preskip"] = int(ms.group(3)), int(ms.group(4)), int(ms.group(5))
                continue
            mv = RE_VAL.match(line)
            if mv:
                ep.setdefault(int(mv.group(1)), {"marks": []})["val_s"] = hms(mv.group(2))
                continue
            ml = RE_VLOSS.match(line)
            if ml:
                ep.setdefault(int(ml.group(1)), {"marks": []})["val_loss"] = float(ml.group(2))
                continue
            if RE_ABORT.match(line):
                abort = True
    if ep or abort:
        sessions.append((ver, ep, abort, last))
    return sessions


def parse_guard(path):
    """gpu_guard.log -> list of (window_end_ts, run_frac, avg_thr, has_targets)."""
    out = []
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = RE_OK.match(line)
            if m:
                out.append((dt.datetime.strptime(m.group(1), TS), float(m.group(2)), float(m.group(3)),
                            bool(m.group(4))))
    return out


def run_frac_in(guard, t0, t1):
    """Mean run_frac of guard windows (10 min, ending at ts) overlapping [t0, t1]; None if none."""
    vals = [f for (ts, f, _, tg) in guard if tg and ts - dt.timedelta(minutes=10) < t1 and ts > t0]
    return statistics.fmean(vals) if vals else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs-dir", default="D:/forge_nnue_train/runs")
    ap.add_argument("--run", default="npt_k32h3_*", help="glob of run names (adapter log = <run>.log)")
    ap.add_argument("--last", type=int, default=0, help="only the N newest runs by adapter-log mtime (0 = all)")
    ap.add_argument("--guard", default="F:/forge_nnue_train/gpu_guard.log", help="'' to skip the run_frac join")
    ap.add_argument("--batch", type=int, default=16384)
    ap.add_argument("--summary", action="store_true", help="per-run lines only")
    a = ap.parse_args()

    logs = [p for p in glob.glob(os.path.join(a.runs_dir, a.run + ".log")) if ".resume" not in os.path.basename(p)]
    logs.sort(key=os.path.getmtime)
    if a.last:
        logs = logs[-a.last:]
    if not logs:
        print("no adapter log matched", file=sys.stderr)
        return 2
    guard = parse_guard(a.guard)
    cols = ["run", "try", "epoch", "end", "wall_min", "train_min", "its", "kept_pos_s", "seg_its", "preskip_x",
            "val_s", "overhead_s", "run_frac", "running_its", "val_loss"]
    if not a.summary:
        print("\t".join(cols))
    print_rows = []
    summary = []
    for lp in logs:
        run = os.path.basename(lp)[:-4]
        tries = parse_adapter(lp)
        for rp in sorted(glob.glob(os.path.join(a.runs_dir, run + ".resume*.log"))):
            tries += parse_adapter(rp)
        trylogs = glob.glob(os.path.join(a.runs_dir, run, "npt_try*.log"))
        sessions = []
        for p in trylogs:
            sessions += parse_try_log(p)
        # trainer sessions are ordered by their version_K folder (one per trainer start, across launch and resumes);
        # adapter tries are ordered by start time: pair them in that order.
        sessions.sort(key=lambda s: s[0])
        tries.sort(key=lambda t: t["start"])
        epochs_seen = {}
        aborts = 0
        backoff = 0
        soft = 0
        abort_at = []
        lost_partial = 0.0
        kept_epoch_min = 0.0
        n_epochs = 0
        last_prev = {}
        for i, t in enumerate(tries):
            _, ep, abort, last = sessions[i] if i < len(sessions) else (-1, {}, False, None)
            if t["exit"] == 97:
                aborts += 1
            backoff += t["backoff"]
            soft += t["soft"]
            if abort and last:
                # training minutes thrown away by the abort: the elapsed time at the last progress mark of the epoch
                # that was running (or had just finished its steps, 100 %, and died in validation / checkpoint save)
                # unless that epoch's checkpoint was recorded by this try
                marks = ep.get(last[0], {}).get("marks") or []
                if marks and last[0] not in {c[1] for c in t["ckpts"]}:
                    lost_partial += marks[-1][3] / 60.0
                    abort_at.append(f"e{last[0]}@{last[1]}%")
                else:
                    abort_at.append(f"e{last[0]}@ckpt")
            elif abort:
                abort_at.append("startup")
            prev = t["start"]
            for (ts, e, step) in t["ckpts"]:
                d = ep.get(e, {})
                wall = (ts - prev).total_seconds() / 60.0
                train_s = d.get("train_s")
                its = d.get("its")
                val_s = d.get("val_s")
                seg = ""
                marks = d.get("marks", [])
                if len(marks) >= 2:
                    rates = []
                    for (m0, m1) in zip(marks, marks[1:]):
                        dsteps = m1[1] - m0[1]
                        dsec = m1[3] - m0[3]
                        rates.append(dsteps / dsec if dsec > 0 else 0.0)
                    rates.insert(0, marks[0][1] / marks[0][3] if marks[0][3] > 0 else 0.0)
                    seg = "/".join(f"{r:.1f}" for r in rates)
                pre = ""
                if "preskip" in d:
                    pk = last_prev.get("preskip")
                    if pk:
                        dp, dtot = d["preskip"] - pk[0], d["total"] - pk[1]
                        pre = f"{dp / dtot:.2f}" if dtot > 0 else ""
                    else:
                        pre = f"{d['preskip'] / d['total']:.2f}" if d.get("total") else ""
                    last_prev["preskip"] = (d["preskip"], d["total"])
                rf = run_frac_in(guard, prev, ts) if guard else None
                overhead = (wall * 60 - (train_s or 0) - (val_s or 0)) if train_s is not None else None
                epochs_seen[e] = epochs_seen.get(e, 0) + 1
                n_epochs += 1
                kept_epoch_min += wall
                row = [run, str(t["n"]), str(e), ts.strftime("%m-%d %H:%M"), f"{wall:.1f}",
                       f"{train_s / 60:.1f}" if train_s else "", f"{its:.2f}" if its else "",
                       f"{its * a.batch / 1000:.0f}k" if its else "", seg, pre,
                       str(val_s) if val_s is not None else "", f"{overhead:.0f}" if overhead is not None else "",
                       f"{rf:.2f}" if rf is not None else "", f"{its / rf:.1f}" if (its and rf) else "",
                       f"{d['val_loss']:.6f}" if "val_loss" in d else ""]
                print_rows.append(row)
                prev = ts
        if tries:
            # active wall = sum of each try's span (start line -> child exit or last checkpoint) + its backoff minutes;
            # gaps between adapter invocations (a resume a day later) are not the run's time.
            wall_h = 0.0
            for t in tries:
                t_end = max([t["exit_ts"] or t["start"]] + [c[0] for c in t["ckpts"]])
                wall_h += (t_end - t["start"]).total_seconds() / 3600.0 + t["backoff"] / 60.0
            twice = sum(v - 1 for v in epochs_seen.values() if v > 1)
            summary.append((run, len(tries), aborts, soft, n_epochs, twice, backoff, lost_partial, wall_h,
                            kept_epoch_min, ",".join(abort_at)))
    if not a.summary:
        for r in print_rows:
            print("\t".join(r))
        print()
    print("run\ttries\taborts97\tsoft_susp\tepochs_done\tepochs_repeated\tbackoff_min\tlost_train_min\twall_h\tepoch_share\tabort_at")
    for (run, nt, ab, so, ne, tw, bo, lp, wh, km, aa) in summary:
        # epoch_share = minutes spent inside checkpointed epochs (repeated ones included) / active wall minutes of the
        # run; the rest is start-up, backoff and training thrown away by aborts (lost_train_min, where abort_at says
        # at which epoch / progress mark each abort hit; "@100%" = died in the end-of-epoch validation / checkpoint).
        share = km / max(wh * 60, 1e-9)
        print(f"{run}\t{nt}\t{ab}\t{so}\t{ne}\t{tw}\t{bo}\t{lp:.0f}\t{wh:.2f}\t{share:.2f}\t{aa}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
