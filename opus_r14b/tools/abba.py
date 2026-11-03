#!/usr/bin/env python3
"""abba.py - Opus R14-B: palindromic A/B timing of any two commands on the shared PC (own code).

  abba.py --out NEW_DIR --a "CMD A" --b "CMD B" [--pairs 6] [--metric REGEX [--higher-better]]
          [--identity REGEX [--identity-ab]] [--mask 0xC] [--priority Idle|BelowNormal] [--cwd DIR]
          [--shell bash|cmd] [--warmup 0] [--load-seconds 3] [--load-every 0]

Slots run A B, B A, A B, ... (pair i = the two runs of slot i; every two slots form one ABBA, so a linear drift
cancels). The driver pins itself to --mask at --priority before it starts anything; Windows children inherit both.
Value per run: wall seconds (lower is better) or, with --metric, the number in group 1 of the LAST match of REGEX in
the run's stdout + stderr (commas removed; add --higher-better for rates). Per pair: speed-up of B over A = A/B for
times, B/A for rates; summary: geometric mean with a two-sided 95 % Student-t interval on the log ratios, median,
min, max. --identity REGEX: every run's output must match, and every run of one command must give the same list of
matches (all groups); --identity-ab also requires A = B (same labels, hash, bench nodes). A difference stops the
driver at once (exit 2). The same command twice (--a X --b X) measures the A/A noise floor.
Load: cpu_users.ps1 (next to this file) samples who uses the CPUs of --mask before the first pair, after the last
and every --load-every pairs; load.txt keeps it - quote it next to the number (Idle work yields to the crew).
Outputs in --out (refused when it exists; nothing is overwritten): runs.tsv, runs/<slot>_<arm>.txt (each run's
output), load.txt, summary.txt. Exit: 0 done, 1 a run exited nonzero, 2 bad arguments / identity differs / metric
missing. No timeout: a hung command blocks the driver (look at the process list; the session tools cannot stop it).
Wall seconds include starting the shell (Git Bash: tens of ms, the same for both arms, pulling the ratio towards 1):
for commands shorter than a few seconds time inside the program and use --metric. --shell cmd passes the command
to cmd.exe /s /c (no inner double quotes there); bash is the tested default.
"""
import argparse
import ctypes
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042}
PRIORITY = {"Idle": 0x40, "BelowNormal": 0x4000}


def t975(df):
    """Two-sided 95 % Student-t quantile: table to df 30, Cornish-Fisher expansion above (error < 0.001)."""
    if df in T975:
        return T975[df]
    z = 1.959964
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df * df)


def pin_self(mask, priority):
    cpus = [i for i in range(64) if mask >> i & 1]
    if os.name == "nt":
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.GetCurrentProcess.restype = ctypes.c_void_p
        h = ctypes.c_void_p(k32.GetCurrentProcess())
        if not k32.SetPriorityClass(h, PRIORITY[priority]):
            raise OSError(ctypes.get_last_error(), "SetPriorityClass")
        if not k32.SetProcessAffinityMask(h, ctypes.c_size_t(mask)):
            raise OSError(ctypes.get_last_error(), "SetProcessAffinityMask")
    else:
        os.sched_setaffinity(0, cpus)
        os.nice(19 if priority == "Idle" else 10)


def shell_argv(kind, cmd):
    if kind == "cmd":
        return ["cmd.exe", "/d", "/s", "/c", cmd]
    git_bash = r"C:\Program Files\Git\bin\bash.exe"
    bash = git_bash if os.name == "nt" and os.path.exists(git_bash) else shutil.which("bash")
    if not bash or "system32" in bash.lower():  # System32\bash.exe is WSL, not Git Bash
        sys.exit(f"abba: no Git Bash found (got {bash}); use --shell cmd or install Git for Windows")
    return [bash, "-c", cmd]


def load_sample(out, label, mask, seconds):
    ps1 = os.path.join(HERE, "cpu_users.ps1")
    if os.name != "nt" or not os.path.exists(ps1) or seconds <= 0:
        text = "(no load sample: cpu_users.ps1 missing, not Windows or --load-seconds 0)\n"
    else:
        r = subprocess.run(["powershell", "-NoProfile", "-File", ps1, "-Mask", hex(mask), "-Seconds", str(seconds)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    with open(os.path.join(out, "load.txt"), "a", encoding="utf-8", newline="\n") as f:
        f.write(f"== {label}\n{text}")
    return text


def run_once(a, argv, out, tag):
    t0 = time.perf_counter()
    r = subprocess.run(argv, cwd=a.cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       creationflags=PRIORITY[a.priority] if os.name == "nt" else 0)
    wall = time.perf_counter() - t0
    text = r.stdout.decode("utf-8", "replace")
    with open(os.path.join(out, "runs", tag + ".txt"), "x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return wall, text, r.returncode


def value_of(a, wall, text, tag):
    if not a.metric:
        return wall
    hits = list(re.finditer(a.metric, text))
    if not hits:
        print(f"abba: --metric found nothing in run {tag} (output in runs/{tag}.txt)", file=sys.stderr)
        sys.exit(2)
    try:
        v = float((hits[-1].group(1) or "").replace(",", ""))  # commas = thousands separators
    except ValueError:
        print(f"abba: run {tag}: --metric group 1 is {hits[-1].group(1)!r}, not a number", file=sys.stderr)
        sys.exit(2)
    if v <= 0:
        print(f"abba: run {tag} gave metric {v} (must be > 0)", file=sys.stderr)
        sys.exit(2)
    return v


def identity_of(a, text, tag):
    if not a.identity:
        return ""
    hits = re.findall(a.identity, text)
    if not hits:
        print(f"abba: --identity found nothing in run {tag} (output in runs/{tag}.txt)", file=sys.stderr)
        sys.exit(2)
    return repr(hits)


def summarize(vals, higher):
    s = [b / a if higher else a / b for a, b in vals]
    logs = [math.log(x) for x in s]
    m = statistics.fmean(logs)
    half = t975(len(logs) - 1) * statistics.stdev(logs) / math.sqrt(len(logs)) if len(logs) > 1 else float("nan")
    return s, math.exp(m), math.exp(m - half), math.exp(m + half)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, help="new folder for the logs (refused when it exists)")
    ap.add_argument("--a", required=True, help="command A (the reference)")
    ap.add_argument("--b", required=True, help="command B")
    ap.add_argument("--pairs", type=int, default=6)
    ap.add_argument("--metric", help="regex whose group 1 is the value (default: wall seconds)")
    ap.add_argument("--higher-better", action="store_true", help="the metric is a rate")
    ap.add_argument("--identity", help="regex; its matches must agree between runs of one command")
    ap.add_argument("--identity-ab", action="store_true", help="the identity must also agree between A and B")
    ap.add_argument("--mask", default="0xC", help="CPU mask for the driver and its children (default 0xC)")
    ap.add_argument("--priority", choices=sorted(PRIORITY), default="Idle")
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--shell", choices=("bash", "cmd"), default="bash")
    ap.add_argument("--warmup", type=int, default=0, help="untimed runs of A and B before the first slot")
    ap.add_argument("--load-seconds", type=int, default=3)
    ap.add_argument("--load-every", type=int, default=0, help="also sample the load every N pairs (0 = ends only)")
    a = ap.parse_args()
    if a.pairs < 2:
        ap.error("--pairs must be >= 2 (one ABBA)")
    if a.higher_better and not a.metric:
        ap.error("--higher-better needs --metric")
    if a.identity_ab and not a.identity:
        ap.error("--identity-ab needs --identity")
    for rx in (a.metric, a.identity):
        if rx:
            try:
                re.compile(rx)
            except re.error as e:
                ap.error(f"bad regex {rx!r}: {e}")
    if a.metric and re.compile(a.metric).groups < 1:
        ap.error("--metric needs a capture group, e.g. 'rows/h ([0-9,.]+)'")
    try:
        mask = int(a.mask, 16)
    except ValueError:
        ap.error(f"--mask {a.mask!r} is not a hex CPU mask (e.g. 0xC)")
    if mask <= 0 or mask >= 1 << (os.cpu_count() or 64):
        ap.error(f"--mask {a.mask} names no CPU or a CPU this PC does not have ({os.cpu_count()} logical CPUs)")
    if os.path.exists(a.out):
        ap.error(f"--out {a.out} exists (write fresh, named folders)")
    try:
        pin_self(mask, a.priority)
    except OSError as e:
        ap.error(f"cannot pin the driver to {a.mask} at {a.priority}: {e}")
    os.makedirs(os.path.join(a.out, "runs"), exist_ok=False)
    argv = {"A": shell_argv(a.shell, a.a), "B": shell_argv(a.shell, a.b)}
    start = time.strftime("%Y-%m-%d %H:%M:%S")
    head = [f"abba.py start {start} pairs {a.pairs} mask {a.mask} priority {a.priority} shell {a.shell}",
            f"A: {a.a}", f"B: {a.b}", f"cwd: {a.cwd or os.getcwd()}",
            f"value: {'metric ' + repr(a.metric) + (' (higher is better)' if a.higher_better else ' (lower is better)') if a.metric else 'wall seconds (lower is better)'}",
            f"identity: {a.identity!r}{' (A = B required)' if a.identity_ab else ''}" if a.identity else "identity: none"]
    print("\n".join(head), flush=True)
    load_sample(a.out, "before", mask, a.load_seconds)
    for w in range(a.warmup):
        for arm in "AB":
            _, _, rc = run_once(a, argv[arm], a.out, f"warmup{w}_{arm}")
            if rc:
                print(f"abba: warm-up run {arm} exited {rc} (runs/warmup{w}_{arm}.txt)", file=sys.stderr)
                return 1
    rows, ids, vals = [], {"A": None, "B": None}, []
    with open(os.path.join(a.out, "runs.tsv"), "x", encoding="utf-8", newline="\n") as tsv:
        tsv.write("slot\torder\tarm\twall_s\tvalue\texit\tidentity\n")
        for slot in range(a.pairs):
            order = "AB" if slot % 2 == 0 else "BA"
            got = {}
            for arm in order:
                tag = f"{slot:03d}_{arm}"
                wall, text, rc = run_once(a, argv[arm], a.out, tag)
                ident = identity_of(a, text, tag) if rc == 0 else ""
                v = value_of(a, wall, text, tag) if rc == 0 else float("nan")
                tsv.write(f"{slot}\t{order}\t{arm}\t{wall:.3f}\t{v:.6g}\t{rc}\t{ident}\n")
                tsv.flush()
                if rc:
                    print(f"abba: run {tag} exited {rc} (runs/{tag}.txt)", file=sys.stderr)
                    return 1
                if ids[arm] is None:
                    ids[arm] = ident
                elif ident != ids[arm]:
                    print(f"abba: identity of {tag} differs from the first {arm} run: {ident} vs {ids[arm]}",
                          file=sys.stderr)
                    return 2
                if a.identity_ab and ids["A"] is not None and ids["B"] is not None and ids["A"] != ids["B"]:
                    print(f"abba: identity A {ids['A']} != B {ids['B']} (--identity-ab)", file=sys.stderr)
                    return 2
                got[arm] = v
            vals.append((got["A"], got["B"]))
            print(f"slot {slot} {order}: A {got['A']:.6g} B {got['B']:.6g}", flush=True)
            if a.load_every and (slot + 1) % a.load_every == 0 and slot + 1 < a.pairs:
                load_sample(a.out, f"after pair {slot + 1}", mask, a.load_seconds)
    after = load_sample(a.out, "after", mask, a.load_seconds)
    s, gm, lo, hi = summarize(vals, a.higher_better)
    what = "B/A" if a.higher_better else "A/B"
    lines = head + [
        f"A median {statistics.median(v[0] for v in vals):.6g}, B median {statistics.median(v[1] for v in vals):.6g}",
        f"speed-up of B over A ({what} per pair): " + " ".join(f"{x:.4f}" for x in s),
        f"geometric mean {gm:.4f}, 95% CI {lo:.4f} .. {hi:.4f} (Student t on log ratios, n={len(s)}); "
        f"median {statistics.median(s):.4f}, min {min(s):.4f}, max {max(s):.4f}",
        f"identity: {'A = B' if a.identity and ids['A'] == ids['B'] else 'A != B' if a.identity else 'not checked'}"
        + (f"; A {ids['A'][:80]}" if a.identity else ""),
        "load after the last pair (CPUs of the mask; full samples in load.txt):",
        *("  " + x for x in (after.strip().splitlines()[1:6] or after.strip().splitlines())),
        f"end {time.strftime('%Y-%m-%d %H:%M:%S')} - ADVISORY on a shared PC (quote the load; QA times officially)"]
    with open(os.path.join(a.out, "summary.txt"), "x", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[len(head):]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
