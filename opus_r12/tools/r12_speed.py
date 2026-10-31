#!/usr/bin/env python3
"""r12_speed.py - R12 bench-speed comparison of Forge exes: palindromic ABBA blocks, fresh process per run.

  r12_speed.py --out DIR --cpu N --exe TAG=PATH [--exe TAG=PATH ...] --ref TAG [--net PATH] --pairs 7
               [--aa TAG=COPYPATH ...] [--aa-pairs 3] [--depths 16 20] [--seed 20261030] [--max-load 0.97]

Each block runs the exes in the order E1 E2 ... Ek Ek ... E2 E1 (k=2 is plain ABBA), so every pair of exes sits in an
ABBA pattern inside the block and a linear drift cancels for every comparison. A/A blocks use byte copies (--aa
TAG=COPY: the copy runs as TAG'); a copy is a different file, so the A/A also shows per-file effects (R5B lesson).
Every run: new process at BelowNormal pinned to CPU N; uci; Threads 1, Hash 16, OwnBook false, [EvalFileHalfKA net];
isready; bench D; quit. Records the engine's bench nodes / ms / nps and the process CPU seconds of the bench window.
Per comparison X vs REF and depth: ratio per block = (nps X1 + nps X2) / (nps R1 + nps R2); gain = ratio - 1;
median, bootstrap of the median (10000 resamples, seeded): one-sided 95% lower bound (5th pct) and 2-sided 95% CI.
Nodes of every run must equal the first run of the same exe and depth (else FAIL). Runs only while the CPU pair is
free (--guard-mask: no gate/trainer/self-play process may hold those CPUs); waits otherwise.
"""
import argparse
import csv
import json
import os
import random
import re
import statistics
import subprocess
import sys
import time

import psutil

BELOW_NORMAL = 0x00004000


def busy_masks(guard_mask, ignore_idle=False):
    """Processes that are not ours and whose affinity covers a CPU of guard_mask (gates, trainer, self-play, QA).
    ignore_idle: Idle-class processes (trainer, self-play) do not count - only when QA freed the pair for R12."""
    hits = []
    for p in psutil.process_iter(["pid", "name"]):
        name = (p.info["name"] or "").lower()
        if not (name.startswith("forge") or name.startswith("fastchess") or name.startswith("python")):
            continue
        if p.pid == os.getpid():
            continue
        try:
            aff = p.cpu_affinity()
            cmd = " ".join(p.cmdline())
            idle = p.nice() == psutil.IDLE_PRIORITY_CLASS
        except (psutil.Error, OSError):
            continue
        if ignore_idle and idle:
            continue
        mask = sum(1 << c for c in aff)
        if mask & guard_mask and mask != 0xFFFF and "opus_scratch" not in cmd and "opus_r12" not in cmd:
            hits.append((p.pid, name, hex(mask)))
    return hits


IGNORE_IDLE = False


MIN_FREE_GB = 5.0  # R12 rule: keep about 4 GB of RAM free (+1 GB margin for our engines)


def wait_free(guard_mask, log):
    while True:
        hits = busy_masks(guard_mask, IGNORE_IDLE)
        free_gb = psutil.virtual_memory().available / 2 ** 30
        if not hits and free_gb >= MIN_FREE_GB:
            return
        log("WAIT cpu pair %s busy %s, free RAM %.1f GB" % (hex(guard_mask), hits[:4], free_gb))
        time.sleep(30)


def one_run(exe, depth, cpu, net):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         creationflags=BELOW_NORMAL)
    ps = psutil.Process(p.pid)
    ps.cpu_affinity([cpu])

    def send(s):
        p.stdin.write((s + "\n").encode())
        p.stdin.flush()

    def wait(rx):
        r = re.compile(rx)
        seen = []
        for b in iter(p.stdout.readline, b""):
            line = b.decode("utf-8", "replace").rstrip("\r\n")
            seen.append(line)
            m = r.search(line)
            if m:
                return m, seen
        raise RuntimeError("engine exited before %s; last %s" % (rx, seen[-3:]))

    send("uci")
    wait(r"^uciok")
    for s in ("setoption name Threads value 1", "setoption name Hash value 16", "setoption name OwnBook value false"):
        send(s)
    if net:
        send("setoption name EvalFileHalfKA value " + net)
    send("isready")
    _, seen = wait(r"^readyok")
    if net and not any(l.startswith("info string EvalFileHalfKA loaded") for l in seen):
        raise RuntimeError("net not loaded: %s" % seen[-3:])
    if any("ERROR" in l for l in seen):
        raise RuntimeError("engine error: %s" % seen)
    c0 = ps.cpu_times()
    send("bench %d" % depth)
    m, _ = wait(r"bench depth %d nodes (\d+) time (\d+) nps (\d+)" % depth)
    c1 = ps.cpu_times()
    send("quit")
    p.stdin.close()
    p.wait(timeout=60)
    cpu_s = (c1.user + c1.system) - (c0.user + c0.system)
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), cpu_s


def boot(gains, seed, n=10000):
    rng = random.Random(seed)
    meds = sorted(statistics.median(rng.choice(gains) for _ in gains) for _ in range(n))
    return meds[int(0.05 * n)], meds[int(0.025 * n)], meds[int(0.975 * n) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cpu", type=int, required=True)
    ap.add_argument("--guard-mask", type=lambda s: int(s, 0), default=None,
                    help="CPUs that must be free of gate/trainer/self-play processes (default: the pair of --cpu)")
    ap.add_argument("--exe", action="append", required=True)
    ap.add_argument("--aa", action="append", default=[])
    ap.add_argument("--ref", action="append", required=True, help="reference tag(s) to compare every other exe with")
    ap.add_argument("--net", default="")
    ap.add_argument("--pairs", type=int, default=7)
    ap.add_argument("--aa-pairs", type=int, default=3)
    ap.add_argument("--depths", type=int, nargs="+", default=[16, 20])
    ap.add_argument("--seed", type=int, default=20261030)
    ap.add_argument("--ignore-idle", action="store_true",
                    help="QA freed the pair for R12: Idle-class processes (trainer, self-play) do not block it")
    a = ap.parse_args()
    global IGNORE_IDLE
    IGNORE_IDLE = a.ignore_idle
    os.makedirs(a.out, exist_ok=True)
    guard = a.guard_mask if a.guard_mask is not None else (3 << (a.cpu & ~1))
    exes = dict(x.split("=", 1) for x in a.exe)
    order = [x.split("=", 1)[0] for x in a.exe]
    aas = dict(x.split("=", 1) for x in a.aa)
    logf = open(os.path.join(a.out, "speed.log"), "a", encoding="utf-8", newline="\n")

    def log(msg):
        line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    log("start cpu %d guard %s net %s exes %s aa %s refs %s pairs %d aa_pairs %d depths %s" % (
        a.cpu, hex(guard), a.net or "none", exes, aas, a.ref, a.pairs, a.aa_pairs, a.depths))
    csv_path = os.path.join(a.out, "runs.csv")
    new_file = not os.path.exists(csv_path)
    cf = open(csv_path, "a", newline="", encoding="utf-8")
    cw = csv.writer(cf, lineterminator="\n")
    if new_file:
        cw.writerow(["pc_time", "phase", "block", "depth", "slot", "tag", "nodes", "ms", "nps", "cpu_s", "cpu_nps"])
    nodes_seen, res = {}, {}

    def rec(phase, block, depth, slot, tag, path):
        nodes, ms, nps, cpu_s = one_run(path, depth, a.cpu, a.net)
        key = (tag.rstrip("'"), depth)
        if key in nodes_seen and nodes_seen[key] != nodes:
            log("FAIL nodes %s d%d %d != %d" % (tag, depth, nodes, nodes_seen[key]))
            sys.exit(2)
        nodes_seen.setdefault(key, nodes)
        cpu_nps = nodes / cpu_s if cpu_s > 0 else 0.0
        cw.writerow([time.strftime("%Y-%m-%dT%H:%M:%S"), phase, block, depth, slot, tag, nodes, ms, nps,
                     "%.4f" % cpu_s, "%.0f" % cpu_nps])
        cf.flush()
        res.setdefault((phase, depth, block), {}).setdefault(tag, []).append((nps, cpu_nps))

    for depth in a.depths:
        for blk in range(1, a.pairs + 1):
            wait_free(guard, log)
            seq = order + order[::-1]
            for slot, tag in enumerate(seq):
                rec("ABBA", blk, depth, slot, tag, exes[tag])
            log("d%d ABBA block %d done" % (depth, blk))
        if aas:
            aa_order = []
            for tag in order:
                if tag in aas:
                    aa_order += [tag, tag + "'"]
            paths = dict(exes)
            paths.update({t + "'": p for t, p in aas.items()})
            for blk in range(1, a.aa_pairs + 1):
                wait_free(guard, log)
                seq = aa_order + aa_order[::-1]
                for slot, tag in enumerate(seq):
                    rec("AA", blk, depth, slot, tag, paths[tag])
                log("d%d AA block %d done" % (depth, blk))

    summary = {"cpu": a.cpu, "net": a.net, "exes": exes, "aa": aas, "nodes": {"%s d%d" % k: v for k, v in nodes_seen.items()},
               "comparisons": []}
    out_lines = []
    for depth in a.depths:
        blocks = sorted(b for (ph, d, b) in res if ph == "ABBA" and d == depth)
        for ref in a.ref:
            for tag in order:
                if tag == ref:
                    continue
                for metric, idx in (("engine_nps", 0), ("cpu_nps", 1)):
                    gains = []
                    for b in blocks:
                        r = res[("ABBA", depth, b)]
                        den = sum(v[idx] for v in r[ref])
                        if den > 0:
                            gains.append(sum(v[idx] for v in r[tag]) / den - 1.0)
                    if len(gains) != len(blocks):
                        out_lines.append("d%d %s vs %s %s: zero time in some run (depth too small), skipped" % (
                            depth, tag, ref, metric))
                        continue
                    med = statistics.median(gains)
                    lb, lo, hi = boot(gains, a.seed)
                    item = {"depth": depth, "x": tag, "ref": ref, "metric": metric, "n": len(gains), "gains": gains,
                            "median": med, "lb95_one_sided": lb, "ci95": [lo, hi]}
                    summary["comparisons"].append(item)
                    out_lines.append("d%d %-12s vs %-12s %-10s n=%d median %+.2f%%  boot 1-sided 95%% LB %+.2f%%  "
                                     "2-sided [%+.2f%%, %+.2f%%]  blocks %s" % (
                                         depth, tag, ref, metric, len(gains), 100 * med, 100 * lb, 100 * lo, 100 * hi,
                                         " ".join("%+.2f" % (100 * g) for g in gains)))
        aa_blocks = sorted(b for (ph, d, b) in res if ph == "AA" and d == depth)
        for tag in aas:
            for metric, idx in (("engine_nps", 0), ("cpu_nps", 1)):
                gains = [sum(v[idx] for v in res[("AA", depth, b)][tag]) /
                         sum(v[idx] for v in res[("AA", depth, b)][tag + "'"]) - 1.0 for b in aa_blocks
                         if sum(v[idx] for v in res[("AA", depth, b)][tag + "'"]) > 0]
                if gains and len(gains) == len(aa_blocks):
                    summary["comparisons"].append({"depth": depth, "x": tag, "ref": tag + "'", "metric": metric,
                                                   "n": len(gains), "gains": gains, "median": statistics.median(gains)})
                    out_lines.append("d%d A/A %-12s vs copy    %-10s n=%d median %+.2f%%  blocks %s" % (
                        depth, tag, metric, len(gains), 100 * statistics.median(gains),
                        " ".join("%+.2f" % (100 * g) for g in gains)))
    json.dump(summary, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    with open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out_lines) + "\n")
    for l in out_lines:
        log(l)
    log("ALL DONE")


if __name__ == "__main__":
    main()
