#!/usr/bin/env python3
"""export_times.py - how long a net export (serialize to .nnue) and a checkpoint hand-over take, from file stamps only.

Read-only. Stdlib only. Run: C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B export_times.py [opts]

Exports: <exports-dir>/<run>/<name>.nnue with <name>.nnue.err (created when the export starts, usually empty) and
<name>.nnue.log (the serializer's stdout, written as it goes). Export seconds = mtime(.nnue) - creation time(.err)
(Windows keeps the creation time in st_ctime). Checkpoints: <runs-dir>/<run>/epochNNN-stepS.pt sizes and the
spacing of their mtimes (= epoch wall minutes incl. validation and the save; the adapter links the trainer's
.ckpt, so the mtime is the trainer's write time).
Exit 0; 2 when nothing was found.
"""
import argparse
import datetime as dt
import glob
import os
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exports-dir", default="D:/forge_nnue_train/exports")
    ap.add_argument("--runs-dir", default="D:/forge_nnue_train/runs")
    ap.add_argument("--run", default="npt_k32h3_*", help="glob of run folders for the checkpoint table")
    ap.add_argument("--last", type=int, default=3, help="newest N run folders for the checkpoint table")
    a = ap.parse_args()
    found = 0
    print("export\tstart\tseconds\tnnue_MB\tlog_KB")
    for nn in sorted(glob.glob(os.path.join(a.exports_dir, "*", "*.nnue")), key=os.path.getmtime):
        err = nn + ".err"
        if not os.path.isfile(err):
            continue
        st_e, st_n = os.stat(err), os.stat(nn)
        start = min(st_e.st_ctime, st_e.st_mtime)
        secs = st_n.st_mtime - start
        log = nn + ".log"
        kb = os.path.getsize(log) / 1024 if os.path.isfile(log) else 0
        print(f"{os.path.relpath(nn, a.exports_dir)}\t{dt.datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M:%S')}"
              f"\t{secs:.0f}\t{st_n.st_size / 1e6:.1f}\t{kb:.0f}")
        found += 1
    print()
    print("run\tcheckpoints\tGB_total\tGB_each\tspacing_min(min/median/max)")
    dirs = [d for d in glob.glob(os.path.join(a.runs_dir, a.run)) if os.path.isdir(d)]
    dirs.sort(key=os.path.getmtime)
    for d in dirs[-a.last:]:
        cks = sorted(glob.glob(os.path.join(d, "epoch*-step*.pt")), key=os.path.getmtime)
        if not cks:
            continue
        sizes = [os.path.getsize(c) for c in cks]
        ts = [os.path.getmtime(c) for c in cks]
        gaps = sorted((b - x) / 60 for x, b in zip(ts, ts[1:]))
        sp = f"{gaps[0]:.1f}/{gaps[len(gaps) // 2]:.1f}/{gaps[-1]:.1f}" if gaps else ""
        print(f"{os.path.basename(d)}\t{len(cks)}\t{sum(sizes) / 2**30:.1f}\t{sizes[0] / 2**30:.2f}\t{sp}")
        found += 1
    return 0 if found else 2


if __name__ == "__main__":
    sys.exit(main())
