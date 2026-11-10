"""file_effect.py - does the same exe run equally fast from different files?

K byte-identical copies of one exe are made. In each of R rounds every copy is launched once (fresh process,
warm `bench 13`, timed `bench D`); the order of the copies rotates from round to round. Measured: CPU cycles
of the engine process per node of the timed bench (QueryProcessCycleTime), for every (copy, round).

Analysis on the logarithms, two-way: a round effect (the machine's state drifting while the test runs) and a
copy effect are taken out; what is left is the residual of one launch. Printed: each copy's mean offset from
the grand mean, the SD between copies, the SD of the residual, the F ratio (variance between copies over
residual variance) and a permutation p value (copy labels shuffled inside each round, 20,000 times): the
share of shuffles whose between-copy variance is at least the observed one.

A between-copy SD well above residual / sqrt(R) with a small p means that one exe file carries its own speed
offset for as long as it stays loaded. A timing that compares two fixed files then includes one such offset
per file. INDICATIVE like every timing of this job; meant to be repeated by QA on a quiet machine.

usage: file_effect.py --exe X --out DIR [--copies 6] [--rounds 8] [--depth 16] [--net on|off] [--workdir DIR]
"""
import argparse
import json
import math
import os
import random
import shutil
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402
from spd_uci import Engine, now_vienna, sha256_file  # noqa: E402


def between_var(x, k, r):
    """x[f][j]: log cycles per node of copy f in round j, round means already removed. Variance of copy means."""
    means = [sum(x[f]) / r for f in range(k)]
    g = sum(means) / k
    return sum((m - g) ** 2 for m in means) / (k - 1)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--exe", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--copies", type=int, default=6)
    p.add_argument("--rounds", type=int, default=8)
    p.add_argument("--depth", type=int, default=16)
    p.add_argument("--net", choices=["on", "off"], default="on")
    p.add_argument("--workdir", default=None)
    a = p.parse_args()
    pin = pinguard.ensure()
    print(pin, flush=True)
    os.makedirs(a.out, exist_ok=False)
    work = a.workdir or os.path.join(a.out, "copies")
    os.makedirs(work, exist_ok=True)
    k, r = a.copies, a.rounds
    files = []
    for f in range(k):
        dst = os.path.join(work, f"fe_{os.getpid()}_{f}.exe")
        shutil.copyfile(a.exe, dst)
        files.append(dst)
    net = "true" if a.net == "on" else "false"
    rows = []
    want = None
    started = now_vienna()
    for j in range(r):
        for pos in range(k):
            f = (j + pos) % k
            eng = Engine(files[f])
            base = eng.image_base()
            eng.handshake(["OwnBook=false", f"UseNNUE={net}"])
            eng.bench(13)
            f0, k0, u0 = eng.faults_and_times()
            c0 = eng.cpu_seconds()
            nodes, _ms, wall = eng.bench(a.depth)
            gc = eng.cpu_seconds() - c0
            f1, k1, u1 = eng.faults_and_times()
            eng.close()
            if want is None:
                want = nodes
            if nodes != want:
                raise SystemExit(f"bench nodes {nodes} != {want}")
            rows.append({"round": j, "slot": pos, "copy": f, "cycles_per_node": 1e9 * gc / nodes, "wall_s": wall,
                         "image_base": hex(base), "page_faults": f1 - f0, "kernel_s": round(k1 - k0, 4),
                         "user_s": round(u1 - u0, 4)})
        print(f"round {j}: " + " ".join(f"{x['cycles_per_node']:.0f}" for x in sorted(rows[-k:], key=lambda x: x["copy"])),
              flush=True)
    left = []
    time.sleep(1.0)
    for path in files:
        try:
            os.remove(path)
        except OSError:
            left.append(path)
    # two-way layout on logs
    x = [[0.0] * r for _ in range(k)]
    for row in rows:
        x[row["copy"]][row["round"]] = math.log(row["cycles_per_node"])
    for j in range(r):                                   # remove round means
        m = sum(x[f][j] for f in range(k)) / k
        for f in range(k):
            x[f][j] -= m
    copy_mean = [sum(x[f]) / r for f in range(k)]
    resid = [x[f][j] - copy_mean[f] for f in range(k) for j in range(r)]
    ms_resid = sum(e * e for e in resid) / ((k - 1) * (r - 1))
    obs = between_var(x, k, r)
    f_ratio = (r * obs) / ms_resid if ms_resid > 0 else float("inf")
    rng = random.Random(20261110)
    hits, trials = 0, 20000
    for _ in range(trials):
        y = [[0.0] * r for _ in range(k)]
        for j in range(r):
            col = [x[f][j] for f in range(k)]
            rng.shuffle(col)
            for f in range(k):
                y[f][j] = col[f]
        if between_var(y, k, r) >= obs:
            hits += 1
    # between-copy SD with the share that residual noise alone would give removed
    sd_copy_raw = math.sqrt(obs)
    sd_copy = math.sqrt(max(obs - ms_resid / r, 0.0))
    res = {"label": "INDICATIVE", "exe": a.exe, "sha256": sha256_file(a.exe), "pin": pin, "copies": k, "rounds": r,
           "timed": f"bench {a.depth}", "net": a.net, "started": started, "finished": now_vienna(), "nodes": want,
           "copy_offset_pct": [100 * (math.exp(m) - 1) for m in copy_mean],
           "sd_between_copies_pct_raw": 100 * sd_copy_raw, "sd_between_copies_pct": 100 * sd_copy,
           "sd_residual_pct": 100 * math.sqrt(ms_resid), "f_ratio": f_ratio, "p_permutation": (hits + 1) / (trials + 1),
           "median_cycles_per_node": statistics.median(row["cycles_per_node"] for row in rows),
           "distinct_image_bases": len({row["image_base"] for row in rows}), "left_behind": left, "rows": rows}
    with open(os.path.join(a.out, "FILE_EFFECT.json"), "w", encoding="utf-8", newline="\n") as fo:
        json.dump(res, fo, indent=1)
    print(f"FILE_EFFECT {k} copies x {r} rounds, bench {a.depth} net {a.net}, median {res['median_cycles_per_node']:.0f} cycles/node", flush=True)
    print("  copy offsets (cycles per node, % from the mean; positive = slower): " +
          " ".join(f"{v:+.2f}" for v in res["copy_offset_pct"]), flush=True)
    print(f"  SD between copies {res['sd_between_copies_pct']:.2f} % (raw {res['sd_between_copies_pct_raw']:.2f} %), "
          f"SD of one launch after copy and round are removed {res['sd_residual_pct']:.2f} %, "
          f"F {f_ratio:.1f}, permutation p {res['p_permutation']:.4f}", flush=True)
    for path in left:
        print(f"left behind (own temporary copy): {path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
