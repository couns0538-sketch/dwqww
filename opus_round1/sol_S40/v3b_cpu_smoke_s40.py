#!/usr/bin/env python3
"""CPU smoke: the PC's v3b trainer (a byte-identical renamed copy, run unchanged) trains on a sealed S40 merge output.
usage: python -I -B v3b_cpu_smoke_s40.py --trainer COPY.py --merged OUT_DIR --holdout-pos A.pos B.pos --holdout-hce-dir DIR
                                         --work NEW_DIR [--epochs 2 --batch 128 --shape 16]
Two runs from fresh processes: RAM loading (default) and --mmap-data. Each must load the data, pass --init-check, finish
the epochs with finite losses and export; the two runs must print the same loss lines and write identical .inc/.bin.
Guards: free RAM >= 6 GiB before each run; the NNUE supervisor log must gain no "adopted running job" line; the
trainer copy's name never matches the supervisor's 'train_resid*.py' pattern; no --guard-tag is passed."""
import argparse
import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SUPERVISOR_LOG = Path(r"F:\forge_nnue_train\supervisor.log")


def free_gib():
    class MS(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong), ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                    ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
    m = MS(); m.dwLength = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / (1 << 30)


def adopted_lines():
    if not SUPERVISOR_LOG.exists():
        return None
    with open(SUPERVISOR_LOG, "r", encoding="utf-8", errors="replace") as f:
        return sum("adopted running job" in line for line in f)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trainer", required=True); ap.add_argument("--merged", required=True)
    ap.add_argument("--holdout-pos", nargs="+", required=True); ap.add_argument("--holdout-hce-dir", required=True)
    ap.add_argument("--work", required=True); ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch", type=int, default=128); ap.add_argument("--shape", type=int, default=16)
    a = ap.parse_args()
    trainer = Path(a.trainer).resolve()
    if re.search(r"train_resid\w*\.py", str(trainer)):
        sys.exit("the trainer copy must be renamed (supervisor pattern)")
    work = Path(a.work)
    if work.exists():
        sys.exit(f"{work} exists (never overwritten)")
    view = work / "view"; view.mkdir(parents=True)
    merged = sorted(Path(a.merged).glob("*.pos"))
    for p in merged:
        shutil.copyfile(p, view / p.name); shutil.copyfile(p.with_suffix(".hce"), view / (p.stem + ".hce"))
    hold = []
    for h in a.holdout_pos:
        h = Path(h); shutil.copyfile(h, view / h.name); shutil.copyfile(Path(a.holdout_hce_dir) / (h.stem + ".hce"), view / (h.stem + ".hce"))
        hold.append(str(view / h.name))
    report = {"trainer_sha256": sha(trainer), "merged": [p.name for p in merged], "holdout": [Path(h).name for h in hold], "runs": {}}
    base_adopted = adopted_lines(); report["supervisor_adopted_lines_before"] = base_adopted
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               TMP=str(work), TEMP=str(work))
    outs = {}
    for mode in ("ram", "mmap"):
        if free_gib() < 6.0:
            sys.exit(f"free RAM {free_gib():.1f} GiB < 6: not started")
        run_dir = work / f"s40_v3b_cpu_{mode}"
        argv = [sys.executable, "-B", str(trainer), "--device", "cpu", "--train", *[str(view / p.name) for p in merged],
                "--holdout", *hold, "--hce-dir", str(view), "--shape", str(a.shape), "--residual", "--epochs", str(a.epochs),
                "--batch-size", str(a.batch), "--lr", "0.001", "--warmup-steps", "2", "--val-positions", "0", "--seed", "1",
                "--init-check", "--final-full-val", "--log-every", "1000", "--run-dir", str(run_dir)]
        if mode == "mmap":
            argv.append("--mmap-data")
        t0 = time.monotonic()
        p = subprocess.run(argv, cwd=str(work), env=env, capture_output=True, text=True, creationflags=0x40)  # IDLE
        (work / f"{mode}.stdout").write_text(p.stdout, encoding="utf-8"); (work / f"{mode}.stderr").write_text(p.stderr, encoding="utf-8")
        lines = p.stdout.splitlines()
        exports = sorted(run_dir.glob("*.inc")) + sorted(run_dir.glob("*.bin")) if run_dir.exists() else []
        outs[mode] = {"loss_lines": [re.sub(r" in \d+s", "", l) for l in lines if l.startswith(("EPOCH", "FINAL", "BASELINE", "INIT", "train:", "holdout:"))],
                      "exports": {e.name: sha(e) for e in exports}}
        report["runs"][mode] = {"argv": argv[1:], "returncode": p.returncode, "seconds": round(time.monotonic() - t0, 1),
                                "train_line": next((l for l in lines if l.startswith("train:")), None),
                                "init_check_ok": any("INIT CHECK OK" in l for l in lines),
                                "epoch_lines": [l for l in lines if l.startswith("EPOCH")],
                                "final_line": next((l for l in lines if l.startswith("FINAL")), None),
                                "finished_line": next((l for l in lines if l.startswith("Finished")), None),
                                "exports": outs[mode]["exports"], "stderr_tail": p.stderr.splitlines()[-5:]}
    strip_load = lambda ls: [re.sub(r"\(\d+s( load)?\)", "", l) for l in ls]
    report["ram_equals_mmap_loss_lines"] = strip_load(outs["ram"]["loss_lines"]) == strip_load(outs["mmap"]["loss_lines"])
    report["ram_equals_mmap_exports"] = outs["ram"]["exports"] == outs["mmap"]["exports"] and bool(outs["ram"]["exports"])
    report["supervisor_adopted_lines_after"] = adopted_lines()
    ok = (all(r["returncode"] == 0 and r["init_check_ok"] and r["finished_line"] for r in report["runs"].values())
          and report["ram_equals_mmap_loss_lines"] and report["ram_equals_mmap_exports"]
          and report["supervisor_adopted_lines_after"] == base_adopted)
    report["result"] = "PASS" if ok else "FAIL"
    (work / "v3b_cpu_smoke_report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
