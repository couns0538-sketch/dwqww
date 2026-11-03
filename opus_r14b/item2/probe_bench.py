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
Exit 0 = done (compare: the same answers, none failed); 1 = answers differ, a failed answer or a probe that failed
(abba: no speed figures then); 2 = bad usage or input (a missing or damaged file, no rows / answers, an existing output:
outputs are never overwritten).
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
LOWRUN = os.path.join(HERE, "lowrun.ps1")  # own copy of item 1's launcher (same file, sha256 cc7f28dd...)
TIMING = {"elapsed_ns", "cpu_ns", "process_cpu_ns"}
ROWS_PREFIX = "row_id\tgame_id\tsplit\tfen\t"  # relabel2's rows.tsv and labels.tsv both start with these columns
# Student t, two-sided 95 %, by degrees of freedom (pairs - 1), checked against scipy.stats.t.ppf(0.975, dof);
# 1.96 beyond 30. (Until 2026-11-02 19:15 only 10 pairs used t; other counts used 1.96, a too narrow CI.)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}


class Bad(Exception):
    pass


def fail(msg, code=2):
    """One clear line on stderr and exit; broken input used to end in a Python traceback (bug hunt #14)."""
    print(f"probe_bench: {msg}", file=sys.stderr)
    raise SystemExit(code)


def new_file(path):
    """Refuse an existing output (Start-Process empties its redirect targets) and a missing output folder."""
    if os.path.exists(path):
        fail(f"refusing existing {path} (outputs are never overwritten)")
    if not os.path.isdir(os.path.dirname(os.path.abspath(path))):
        fail(f"{path}: the output folder does not exist")


def need_file(path, what):
    if not os.path.isfile(path):
        fail(f"{what} {path} not found")


def load_answers(path):
    """The probe answers of a JSONL file (one JSON object per line); Bad with the file and line otherwise."""
    rows, n = [], 0
    try:
        with open(path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                if raw.strip():
                    r = json.loads(raw)
                    if not isinstance(r, dict):
                        raise Bad(f"{path}:{n}: not a JSON object")
                    rows.append(r)
    except OSError as e:
        raise Bad(f"{path}: cannot read: {e.strerror or e}")
    except ValueError as e:  # not JSON, or not UTF-8
        raise Bad(f"{path}:{n}: not a JSON answer line: {e}")
    return rows


def cmd_requests(a) -> int:
    if a.start < 0 or a.count < 1:
        fail("--start must be >= 0 and --count >= 1")
    new_file(a.out)
    req = []
    ln = 1
    try:  # read and check everything first: nothing is written for a damaged rows file (bug hunt #14)
        with open(a.rows, "rb") as fh:  # bytes, decoded per used line: a bad byte is reported with its line number
            if not fh.readline().decode("utf-8").startswith(ROWS_PREFIX):
                fail(f"{a.rows}: not a relabel2 rows.tsv / labels.tsv (the first line must start with row_id, "
                     f"game_id, split, fen)")
            for ln, raw in enumerate(fh, 2):
                if ln - 2 < a.start:
                    continue
                if len(req) >= a.count:
                    break
                f = raw.decode("utf-8").rstrip("\r\n").split("\t")
                if len(f) < 4 or not f[3].isascii() or len(f[3].split()) != 6:
                    fail(f"{a.rows}:{ln}: damaged row (no row id and six-field FEN in the first four columns)")
                req.append(f"{f[0]}\tanalyze\t{f[3]}\n")
    except OSError as e:
        fail(f"{a.rows}: cannot read: {e.strerror or e}")
    except UnicodeDecodeError as e:
        fail(f"{a.rows}:{ln}: not UTF-8 text: {e.reason}")
    if not req:
        fail(f"no rows from --start {a.start} in {a.rows}: nothing written")
    with open(a.out, "x", encoding="ascii", newline="\n") as out:
        out.writelines(req)
    print(f"{len(req)} requests -> {a.out}")
    return 0


def run_probe(exe, req, out, mask, nodes):
    need_file(exe, "probe")
    need_file(req, "request file")
    err = out + ".err"
    t0 = time.perf_counter()
    p = subprocess.run(["powershell", "-NoProfile", "-File", LOWRUN, "-Mask", mask, "-Priority", "BelowNormal",
                        "-Exe", os.path.abspath(exe), "-ArgLine", f"--nodes {nodes} --hash-mb 1", "-In",
                        os.path.abspath(req), "-Out", os.path.abspath(out), "-Err", os.path.abspath(err)])
    wall = time.perf_counter() - t0
    if p.returncode:  # was check=True: a traceback (bug hunt #14)
        raise SystemExit(f"{exe}: exit {p.returncode} (127 = could not be started); its stderr is in {err}")
    try:
        rows = load_answers(out)
    except Bad as e:
        raise SystemExit(f"{exe}: {e}")
    if not rows or not all(r.get("ok") for r in rows):
        raise SystemExit(f"{exe}: missing or failed answers in {out}")
    return wall, rows


def cmd_run(a) -> int:
    if a.nodes < 1:
        fail("--nodes must be >= 1")
    new_file(a.out)  # Start-Process used to empty an existing OUT before the probe even started (bug hunt #14)
    new_file(a.out + ".err")
    wall, rows = run_probe(a.exe, a.req, a.out, a.mask, a.nodes)
    print(f"{len(rows)} answers in {wall:.2f} s = {len(rows) / wall:.1f} positions/s -> {a.out}")
    return 0


def stable(row):
    return {k: v for k, v in row.items() if k not in TIMING}


def cmd_compare(a) -> int:
    try:
        ra, rb = load_answers(a.a), load_answers(a.b)
    except Bad as e:
        fail(str(e))
    if not ra or not rb:  # two empty files used to compare as identical, exit 0 (bug hunt #14)
        fail(f"no answers in {a.a if not ra else a.b}: nothing to compare")
    failed = [sum(r.get("ok") is not True for r in rows) for rows in (ra, rb)]
    ra, rb = [stable(r) for r in ra], [stable(r) for r in rb]
    diff = [i for i, (x, y) in enumerate(zip(ra, rb)) if x != y]
    print(f"{a.a} vs {a.b}: {len(ra)} / {len(rb)} answers, {len(ra) - len(diff) if len(ra) == len(rb) else 'n/a'} "
          f"identical, first difference {diff[0] if diff else None}")
    if diff:
        print("  A:", ra[diff[0]])
        print("  B:", rb[diff[0]])
    if len(ra) != len(rb):
        print(f"  NOT the same: A has {len(ra)} answers, B {len(rb)}")
    if any(failed):  # failed answers are no labels, even when both builds fail alike
        print(f"  NOT usable: failed answers (ok is not true) A {failed[0]}, B {failed[1]}")
    return 0 if len(ra) == len(rb) and not diff and not any(failed) else 1


def cmd_abba(a) -> int:
    if a.pairs < 2:  # 0 or 1 pair used to end with exit 0 and no result (bug hunt #14)
        fail("--pairs must be at least 2 (the confidence interval needs two pairs)")
    if a.nodes < 1:
        fail("--nodes must be >= 1")
    if os.path.exists(a.out):
        fail(f"refusing existing {a.out}")
    for path, what in ((a.a, "probe A"), (a.b, "probe B"), (a.req, "request file")):
        need_file(path, what)
    os.makedirs(a.out)
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
    complete = len(speed["A"]) + len(speed["B"]) == len(order)
    if complete:  # a stopped comparison used to print a CI of the runs before the difference and exit 0 (hunt #14)
        ratios = [b / x for x, b in zip(speed["A"], speed["B"])]
        m = statistics.fmean(ratios)
        half = T975.get(len(ratios) - 1, 1.96) * statistics.stdev(ratios) / math.sqrt(len(ratios))
        lines += ["", f"A median {statistics.median(speed['A']):.2f}, B median {statistics.median(speed['B']):.2f} positions/s",
                  "per-pair B/A: " + " ".join(f"{r:.4f}" for r in ratios),
                  f"B/A median {statistics.median(ratios):.4f}, mean {m:.4f}, 95% CI {m - half:.4f} .. {m + half:.4f}",
                  "answers identical in every run"]
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-5:]))
    return 0 if complete else 1


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
