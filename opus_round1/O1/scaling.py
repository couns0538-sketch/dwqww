#!/usr/bin/env python3
"""Lazy SMP scaling table (O1): for each thread count, R runs of `go depth D` over the position set
(fresh ucinewgame per position, Hash 16 by default). Time-to-depth = wall time from `go` to
`bestmove`; NPS = nodes of the last info line / that time. Prints raw per-run totals, then per
thread count: mean total time-to-depth, speedup vs the first thread count, mean NPS, NPS scaling,
and the node overhead (searched nodes vs the first thread count).
usage: scaling.py <engine> --positions <file> [--skip-ids WAC] [--threads 1,2,4,8] [--runs 5] [--depth 20]
                  [--hash 16] [--option Name=Value ...] [--tsv out.tsv]"""
import argparse
import re
import statistics
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from ucilib import Engine  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--positions", required=True)
    ap.add_argument("--skip-ids", default="WAC", help="skip '<FEN> ; <id>' lines whose id starts with this")
    ap.add_argument("--threads", default="1,2,4,8")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--depth", type=int, default=20)
    ap.add_argument("--hash", type=int, default=16)
    ap.add_argument("--option", action="append", default=[])
    ap.add_argument("--tsv")
    a = ap.parse_args()
    positions = []
    for line in open(a.positions, encoding="utf-8"):
        if " ; " in line:
            fen, ident = [x.strip() for x in line.split(" ; ", 1)]
            if a.skip_ids and ident.startswith(a.skip_ids):
                continue
            positions.append((ident, fen))
    eng = Engine(a.engine)
    eng.handshake([("Hash", a.hash), ("OwnBook", "false")] + [tuple(o.split("=", 1)) for o in a.option])
    rows = []
    summary = {}
    for t in [int(x) for x in a.threads.split(",")]:
        eng.send(f"setoption name Threads value {t}")
        eng.ready(60)
        times, nodes_runs = [], []
        for run in range(a.runs):
            total_time, total_nodes = 0.0, 0
            for ident, fen in positions:
                eng.send("ucinewgame")
                eng.ready(60)
                eng.send(f"position fen {fen}")
                t0 = time.perf_counter()
                eng.send(f"go depth {a.depth}")
                _, seen = eng.expect(lambda l: l.startswith("bestmove"), 3600, "bestmove")
                dt = time.perf_counter() - t0
                infos = [l for l in seen if l.startswith(f"info depth {a.depth} ")] or \
                        [l for l in seen if l.startswith("info depth ")]
                m = re.search(r" nodes (\d+)", infos[-1]) if infos else None
                n = int(m.group(1)) if m else 0
                rows.append((t, run, ident, f"{dt:.4f}", n))
                total_time += dt
                total_nodes += n
            times.append(total_time)
            nodes_runs.append(total_nodes)
            print(f"threads {t} run {run}: time-to-depth {total_time:.2f}s nodes {total_nodes} "
                  f"nps {total_nodes / total_time:.0f}", flush=True)
        summary[t] = (statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0,
                      statistics.mean(nodes_runs), statistics.mean(n / s for n, s in zip(nodes_runs, times)))
    eng.quit()
    if a.tsv:
        with open(a.tsv, "w", newline="\n") as fh:
            fh.write("threads\trun\tposition\tseconds\tnodes\n")
            for r in rows:
                fh.write("\t".join(map(str, r)) + "\n")
    first = next(iter(summary))
    print(f"\nscaling: {len(positions)} positions, depth {a.depth}, {a.runs} runs, Hash {a.hash}")
    print("threads | time-to-depth mean (stdev) | speedup | nodes mean | node overhead | NPS mean | NPS scaling")
    for t, (tm, ts, nd, nps) in summary.items():
        print(f"{t:7d} | {tm:10.2f}s ({ts:5.2f}) | {summary[first][0] / tm:6.2f}x | {nd:11.0f} | "
              f"{nd / summary[first][2]:12.2f}x | {nps:9.0f} | {nps / summary[first][3]:6.2f}x")


if __name__ == "__main__":
    main()
