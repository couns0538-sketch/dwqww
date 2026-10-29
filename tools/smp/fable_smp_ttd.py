#!/usr/bin/env python3
"""Time-to-depth measurement for Lazy SMP configurations (job FB2-J5; the R3-6 method in one file).

    fable_smp_ttd.py <forge.exe> <positions.tsv> --threads 1,2,3 --configs off:,on:SmpV2=true --reps 1
                     [--hash 64] [--out results.csv] [--max-positions N]

positions.tsv: `id  class  depth  fen` lines (R3-6 `positions30.tsv`). Every run is a fresh engine process:
uci, Hash, OwnBook false, the config's options, ucinewgame, position fen, go depth D, quit. Measured: wall time
from `go` to `bestmove`, the engine's CPU time (user + kernel, Windows GetProcessTimes), the reported depth and
nodes of the last info line. The runs of one (rep, position) are shuffled over (config, threads) so that load
drift hits every cell alike. Summary: per (config, threads) the sum of wall times, the geometric mean of the
per-position ratios vs the config's Threads=1 run (time-to-depth speedup), node inflation, NPS scaling, CPU
scaling. All numbers are advisory on a loaded PC.
"""
import argparse
import csv
import math
import os
import random
import subprocess
import sys
import time

try:
    import ctypes
    from ctypes import wintypes
    _kernel32 = ctypes.windll.kernel32
except Exception:  # pragma: no cover
    _kernel32 = None


def process_cpu_seconds(handle):
    if _kernel32 is None:
        return 0.0
    c, e, k, u = (wintypes.FILETIME() for _ in range(4))
    if not _kernel32.GetProcessTimes(handle, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return 0.0
    to_s = lambda ft: ((ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 1e7
    return to_s(k) + to_s(u)


def run_one(exe, fen, depth, threads, opts, hash_mb):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def wait(tok):
        last_info = None
        while True:
            line = p.stdout.readline()
            if not line:
                raise RuntimeError("engine died")
            if line.startswith("info depth"):
                last_info = line
            if line.startswith(tok):
                return line.strip(), last_info

    send("uci")
    wait("uciok")
    send(f"setoption name Hash value {hash_mb}")
    send(f"setoption name Threads value {threads}")
    send("setoption name OwnBook value false")
    for o in opts:
        name, value = o.split("=", 1)
        send(f"setoption name {name} value {value}")
    send("ucinewgame")
    send("isready")
    wait("readyok")
    send(f"position fen {fen}")
    send("isready")
    wait("readyok")
    handle = int(p._handle)
    cpu0 = process_cpu_seconds(handle)
    t0 = time.perf_counter()
    send(f"go depth {depth}")
    best, info = wait("bestmove")
    wall = time.perf_counter() - t0
    cpu = process_cpu_seconds(handle) - cpu0
    send("quit")
    p.wait(timeout=10)
    nodes = depth_reported = 0
    if info:
        tok = info.split()
        for i, t in enumerate(tok):
            if t == "nodes":
                nodes = int(tok[i + 1])
            if t == "depth":
                depth_reported = int(tok[i + 1])
    return {"wall": wall, "cpu": cpu, "nodes": nodes, "depth": depth_reported, "bestmove": best.split()[1]}


def gmean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exe")
    ap.add_argument("positions")
    ap.add_argument("--threads", default="1,2,3")
    ap.add_argument("--configs", default="off:,on:SmpV2=true")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--hash", type=int, default=64)
    ap.add_argument("--out", default="smp_ttd.csv")
    ap.add_argument("--max-positions", type=int, default=0)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    positions = []
    for line in open(args.positions):
        if line.startswith("#") or not line.strip():
            continue
        pid, pclass, depth, fen = line.rstrip("\n").split("\t", 3)
        positions.append((pid, pclass, int(depth), fen))
    if args.max_positions:
        positions = positions[:args.max_positions]
    threads = [int(t) for t in args.threads.split(",")]
    configs = []
    for c in args.configs.split(","):
        name, _, opts = c.partition(":")
        configs.append((name, [o for o in opts.split(";") if o]))
    rng = random.Random(args.seed)
    rows = []
    cells = [(cname, copts, t) for cname, copts in configs for t in threads]
    t_start = time.time()
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rep", "id", "class", "depth", "config", "threads", "wall_s", "cpu_s", "nodes", "depth_reported", "bestmove"])
        for rep in range(args.reps):
            for pid, pclass, depth, fen in positions:
                order = cells[:]
                rng.shuffle(order)
                for cname, copts, t in order:
                    r = run_one(args.exe, fen, depth, t, copts, args.hash)
                    row = {"rep": rep, "id": pid, "class": pclass, "depth": depth, "config": cname, "threads": t, **r}
                    rows.append(row)
                    w.writerow([rep, pid, pclass, depth, cname, t, f"{r['wall']:.3f}", f"{r['cpu']:.3f}", r["nodes"], r["depth"], r["bestmove"]])
                    f.flush()
                print(f"rep {rep} {pid} done ({time.time() - t_start:.0f}s)", flush=True)
    # summary: per config/threads, medians per position over reps, then ratios vs the config's T1
    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if len(xs) % 2 else 0.5 * (xs[len(xs) // 2 - 1] + xs[len(xs) // 2])
    print("\n| config | threads | sum wall (s) | speedup (sum) | per-position speedup gmean | nodes Tn/T1 gmean | NPS (M/s) | NPS scaling | CPU Tn/T1 |")
    print("|---|---|---|---|---|---|---|---|---|")
    summary = {}
    for cname, _ in configs:
        base = {}
        for t in threads:
            per = {}
            for pid, _, _, _ in positions:
                sel = [r for r in rows if r["config"] == cname and r["threads"] == t and r["id"] == pid]
                if sel:
                    per[pid] = {"wall": med([r["wall"] for r in sel]), "cpu": med([r["cpu"] for r in sel]), "nodes": med([r["nodes"] for r in sel])}
            if t == threads[0]:
                base = per
            total_wall = sum(v["wall"] for v in per.values())
            total_nodes = sum(v["nodes"] for v in per.values())
            total_cpu = sum(v["cpu"] for v in per.values())
            base_wall = sum(v["wall"] for v in base.values())
            base_nodes = sum(v["nodes"] for v in base.values())
            base_cpu = sum(v["cpu"] for v in base.values())
            sp = gmean([base[p]["wall"] / per[p]["wall"] for p in per if p in base])
            nr = gmean([per[p]["nodes"] / base[p]["nodes"] for p in per if p in base and base[p]["nodes"]])
            nps = total_nodes / total_wall / 1e6 if total_wall else 0
            base_nps = base_nodes / base_wall / 1e6 if base_wall else 0
            summary[(cname, t)] = {"sum_wall": total_wall, "speedup_sum": base_wall / total_wall if total_wall else 0, "speedup_gmean": sp, "nodes_ratio": nr, "nps": nps,
                                   "nps_scaling": nps / base_nps if base_nps else 0, "cpu_ratio": total_cpu / base_cpu if base_cpu else 0}
            s = summary[(cname, t)]
            print(f"| {cname} | {t} | {s['sum_wall']:.1f} | {s['speedup_sum']:.2f} | {s['speedup_gmean']:.2f} | {s['nodes_ratio']:.2f} | {s['nps']:.3f} | {s['nps_scaling']:.2f} | {s['cpu_ratio']:.2f} |")
    # paired comparison on vs off at each thread count
    if len(configs) >= 2:
        a, b = configs[0][0], configs[1][0]
        print(f"\npaired {b} vs {a} (wall ratio gmean over positions, < 1 = {b} faster):")
        for t in threads:
            ratios = []
            for pid, _, _, _ in positions:
                ra = [r["wall"] for r in rows if r["config"] == a and r["threads"] == t and r["id"] == pid]
                rb = [r["wall"] for r in rows if r["config"] == b and r["threads"] == t and r["id"] == pid]
                if ra and rb:
                    ratios.append(med(rb) / med(ra))
            if ratios:
                srt = sorted(ratios)
                print(f"  threads {t}: gmean {gmean(ratios):.3f}, median {srt[len(srt) // 2]:.3f}, {sum(1 for x in ratios if x < 1)}/{len(ratios)} positions faster")


if __name__ == "__main__":
    main()
