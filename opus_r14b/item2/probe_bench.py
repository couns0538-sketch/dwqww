#!/usr/bin/env python3
"""probe_bench.py - Opus R14-B item 2 improvement: check that another build of the relabel probe gives the same labels,
and time it against the current build (own code, stdlib only).

usage:
  probe_bench.py requests --rows ROWS.tsv --start 0 --count 1000 --out REQ.tsv
  probe_bench.py run --exe PROBE --req REQ.tsv --out OUT.jsonl [--mask 0x4] [--nodes 20000]
  probe_bench.py compare A.jsonl B.jsonl          (every answer field except timing; exit 1 on any difference)
  probe_bench.py abba --a PROBE_A --b PROBE_B --req REQ.tsv --pairs 10 --out DIR [--mask 0x4]
Runs go through lowrun.ps1 next to this script (BelowNormal, one CPU), the request file on stdin. Speed = positions per
second of wall time for the whole request file (ADVISORY; the probe's own cpu_ns is recorded too).
"""

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOWRUN = os.path.join(HERE, "lowrun.ps1")  # own copy of item 1's launcher (same file, sha256 2c7fa58f...)
TIMING = {"elapsed_ns", "cpu_ns", "process_cpu_ns"}
# Student t, two-sided 95 %, by degrees of freedom (pairs - 1), checked against scipy.stats.t.ppf(0.975, dof);
# 1.96 beyond 30. (Until 2026-11-02 19:15 only 10 pairs used t; other counts used 1.96, a too narrow CI.)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


def cmd_requests(a) -> int:
    n = 0
    with open(a.rows, encoding="utf-8") as fh, open(a.out, "x", encoding="ascii", newline="\n") as out:
        next(fh)
        for i, line in enumerate(fh):
            if i < a.start:
                continue
            if n >= a.count:
                break
            f = line.rstrip("\n").split("\t")
            out.write(f"{f[0]}\tanalyze\t{f[3]}\n")
            n += 1
    print(f"{n} requests -> {a.out}")
    return 0


def run_probe(exe, req, out, mask, nodes):
    err = out + ".err"
    t0 = time.perf_counter()
    subprocess.run(["powershell", "-NoProfile", "-File", LOWRUN, "-Mask", mask, "-Priority", "BelowNormal",
                    "-Exe", os.path.abspath(exe), "-ArgLine", f"--nodes {nodes} --hash-mb 1", "-In", os.path.abspath(req),
                    "-Out", os.path.abspath(out), "-Err", os.path.abspath(err)], check=True)
    wall = time.perf_counter() - t0
    rows = [json.loads(x) for x in open(out, encoding="utf-8") if x.strip()]
    if not rows or not all(r.get("ok") for r in rows):
        raise SystemExit(f"{exe}: missing or failed answers in {out}")
    return wall, rows


def cmd_run(a) -> int:
    wall, rows = run_probe(a.exe, a.req, a.out, a.mask, a.nodes)
    print(f"{len(rows)} answers in {wall:.2f} s = {len(rows) / wall:.1f} positions/s -> {a.out}")
    return 0


def stable(row):
    return {k: v for k, v in row.items() if k not in TIMING}


def cmd_compare(a) -> int:
    ra = [stable(json.loads(x)) for x in open(a.a, encoding="utf-8") if x.strip()]
    rb = [stable(json.loads(x)) for x in open(a.b, encoding="utf-8") if x.strip()]
    diff = [i for i, (x, y) in enumerate(zip(ra, rb)) if x != y]
    print(f"{a.a} vs {a.b}: {len(ra)} / {len(rb)} answers, {len(ra) - len(diff) if len(ra) == len(rb) else 'n/a'} "
          f"identical, first difference {diff[0] if diff else None}")
    if diff:
        print("  A:", ra[diff[0]])
        print("  B:", rb[diff[0]])
    return 0 if len(ra) == len(rb) and not diff else 1


def cmd_abba(a) -> int:
    os.makedirs(a.out, exist_ok=False)
    order = []
    for p in range(a.pairs):
        order += ["A", "B"] if p % 2 == 0 else ["B", "A"]
    speed = {"A": [], "B": []}
    lines = [f"A = {os.path.abspath(a.a)}", f"B = {os.path.abspath(a.b)}",
             f"requests {a.req}, nodes {a.nodes}, mask {a.mask}, BelowNormal, pairs {a.pairs}", ""]
    ref = None
    for i, arm in enumerate(order):
        exe = a.a if arm == "A" else a.b
        wall, rows = run_probe(exe, a.req, os.path.join(a.out, f"run_{i:02d}_{arm}.jsonl"), a.mask, a.nodes)
        cur = [stable(r) for r in rows]
        if ref is None:
            ref = cur
        elif cur != ref:
            lines.append(f"run {i:02d} {arm}: ANSWERS DIFFER from run 00 - speed comparison invalid")
            print(lines[-1])
            break
        speed[arm].append(len(rows) / wall)
        lines.append(f"run {i:02d} {arm} {len(rows) / wall:.2f} positions/s")
        print(lines[-1], flush=True)
    ratios = [b / x for x, b in zip(speed["A"], speed["B"])]
    if len(ratios) >= 2:
        m = statistics.fmean(ratios)
        half = T975.get(len(ratios) - 1, 1.96) * statistics.stdev(ratios) / math.sqrt(len(ratios))
        lines += ["", f"A median {statistics.median(speed['A']):.2f}, B median {statistics.median(speed['B']):.2f} positions/s",
                  "per-pair B/A: " + " ".join(f"{r:.4f}" for r in ratios),
                  f"B/A median {statistics.median(ratios):.4f}, mean {m:.4f}, 95% CI {m - half:.4f} .. {m + half:.4f}",
                  "answers identical in every run" if len(speed["A"]) + len(speed["B"]) == len(order) else ""]
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-5:]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("requests")
    q.add_argument("--rows", required=True)
    q.add_argument("--start", type=int, default=0)
    q.add_argument("--count", type=int, default=1000)
    q.add_argument("--out", required=True)
    r = sub.add_parser("run")
    r.add_argument("--exe", required=True)
    r.add_argument("--req", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--mask", default="0x4")
    r.add_argument("--nodes", type=int, default=20000)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    b = sub.add_parser("abba")
    b.add_argument("--a", required=True)
    b.add_argument("--b", required=True)
    b.add_argument("--req", required=True)
    b.add_argument("--pairs", type=int, default=10)
    b.add_argument("--out", required=True)
    b.add_argument("--mask", default="0x4")
    b.add_argument("--nodes", type=int, default=20000)
    a = ap.parse_args()
    return {"requests": cmd_requests, "run": cmd_run, "compare": cmd_compare, "abba": cmd_abba}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
