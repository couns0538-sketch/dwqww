#!/usr/bin/env python3
"""S08-2 skew check: how much does turning profiling on slow a Threads>1 search? For each FORGE_PROF exe and
each position, run `go movetime M` with Profile=false and Profile=true in alternating order (fresh process per
run, Hash 16, OwnBook false, Threads T) and take NPS = nodes / time of the last `info` line before bestmove.
The per-arm figure is the median over runs of NPS(on) / NPS(off). With one shared bank of atomic counters
(Sol's TLS v2 design) every node writes the same cache lines from all threads; with per-worker banks
(S08-2) the threads do not share counter lines. Also checks that the Profile=true run prints one counter
packet whose nodes count is at least the reported search nodes (the packet is merged after the helpers stop).
usage: prof_threads_nps.py --threads T --movetime-ms M --runs N --arm NAME=EXE [--arm ...] [--fen FEN ...]"""
import argparse
import hashlib
import os
import re
import statistics
import subprocess
import sys

FENS = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP2BPPP/R2QKB1R w KQ - 0 8"]
INFO = re.compile(r"^info depth \d+ .*?\bnodes (\d+) nps \d+ .*?\btime (\d+)\b")
PACKET_NODES = re.compile(r"^info string prof nodes count (\d+) ")


def run(exe, fen, threads, movetime, profile):
    script = (f"uci\nsetoption name Threads value {threads}\nsetoption name Hash value 16\n"
              f"setoption name OwnBook value false\nsetoption name Profile value {'true' if profile else 'false'}\n"
              f"isready\nucinewgame\nposition fen {fen}\ngo movetime {movetime}\n")
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    p.stdin.write(script)
    p.stdin.flush()
    last, packets, packet_nodes = None, 0, None
    for line in p.stdout:
        line = line.strip()
        m = INFO.match(line)
        if m:
            last = (int(m.group(1)), int(m.group(2)))
        if line.startswith("info string prof schema 1"):
            packets += 1
        m = PACKET_NODES.match(line)
        if m:
            packet_nodes = int(m.group(1))
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n")
    p.stdin.close()
    p.wait(timeout=60)
    nodes, ms = last
    return nodes, ms, nodes * 1000.0 / max(ms, 1), packets, packet_nodes


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, required=True)
    ap.add_argument("--movetime-ms", type=int, default=3000)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--arm", action="append", required=True)
    ap.add_argument("--fen", action="append")
    args = ap.parse_args()
    fens = args.fen or FENS
    print(f"# prof_threads_nps threads {args.threads} movetime {args.movetime_ms} runs {args.runs} "
          f"machine exclusive: {os.environ.get('MACHINE_EXCLUSIVE', 'no')}")
    status = 0
    for spec in args.arm:
        name, exe = spec.split("=", 1)
        print(f"# arm {name}: {exe} sha256 {hashlib.sha256(open(exe, 'rb').read()).hexdigest()}")
        ratios = []
        for f_index, fen in enumerate(fens):
            for r in range(args.runs):
                order = (False, True) if r % 2 == 0 else (True, False)
                res = {}
                for profile in order:
                    nodes, ms, nps, packets, packet_nodes = run(exe, fen, args.threads, args.movetime_ms, profile)
                    res[profile] = nps
                    ok = (packets == 1 and packet_nodes is not None and packet_nodes >= nodes) if profile else packets == 0
                    if not ok:
                        status = 1
                    print(f"{name} fen{f_index} run {r + 1} profile {'on ' if profile else 'off'}: nodes {nodes} "
                          f"time {ms} nps {nps:.0f} packets {packets} packet_nodes {packet_nodes} {'OK' if ok else 'BAD'}",
                          flush=True)
                ratios.append(res[True] / res[False])
        print(f"SUMMARY {name} threads {args.threads}: NPS(on)/NPS(off) median {statistics.median(ratios):.4f} "
              f"mean {statistics.mean(ratios):.4f} min {min(ratios):.4f} max {max(ratios):.4f} n {len(ratios)}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
