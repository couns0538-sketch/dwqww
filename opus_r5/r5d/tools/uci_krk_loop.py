#!/usr/bin/env python3
"""R5D: the KRK mate in 3 over UCI on a real engine exe, many times (end-to-end before/after check).

One engine process per configuration (BelowNormal): setoption Threads / SmpV2 / Hash 16 / OwnBook false, then per run
`ucinewgame`, `isready`, `position fen 4R3/8/8/k2K4/8/8/8/8 w - - 0 1`, `go depth D`; the run fails when the last
`score` of the search is not `mate N` with 3 <= N (a mate for White, never shorter than the true mate in 3).
Run it on a 3-CPU affinity mask (run_pinned.py) when Threads 4 is in the list.
usage: uci_krk_loop.py <exe> --runs 1000 [--depth 14] [--threads 2,4] [--smpv2 0,1] [--label name]
prints one line per configuration: label threads smpv2 depth runs failures exact(mate 3) seconds
"""
import argparse
import re
import subprocess
import time

BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
FEN = "4R3/8/8/k2K4/8/8/8/8 w - - 0 1"


def run_config(exe, threads, smpv2, depth, runs):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         bufsize=1, creationflags=BELOW_NORMAL)

    def send(line):
        p.stdin.write(line + "\n")
        p.stdin.flush()

    def until(prefix):
        lines = []
        while True:
            line = p.stdout.readline()
            if not line:
                raise SystemExit(f"uci_krk_loop: engine exited; last lines {lines[-3:]}")
            line = line.rstrip("\n")
            lines.append(line)
            if line.startswith(prefix):
                return lines

    send("uci")
    until("uciok")
    for name, value in (("Threads", threads), ("Hash", 16), ("OwnBook", "false"), ("SmpV2", "true" if smpv2 else "false")):
        send(f"setoption name {name} value {value}")
    send("isready")
    until("readyok")
    failures = exact = 0
    first_bad = ""
    t0 = time.monotonic()
    for run in range(runs):
        send("ucinewgame")
        send("isready")
        until("readyok")
        send(f"position fen {FEN}")
        send(f"go depth {depth}")
        lines = until("bestmove")
        scores = [l for l in lines if l.startswith("info") and " score " in l]
        m = re.search(r" score mate (-?\d+)", scores[-1]) if scores else None
        n = int(m.group(1)) if m else 0
        if n >= 3:
            exact += 1 if n == 3 else 0
        else:
            failures += 1
            if not first_bad:
                first_bad = f"run {run}: {scores[-1] if scores else 'no score'} | {lines[-1]}"
    seconds = time.monotonic() - t0
    send("quit")
    p.wait(timeout=10)
    return failures, exact, seconds, first_bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--runs", type=int, default=1000)
    ap.add_argument("--depth", type=int, default=14)
    ap.add_argument("--threads", default="2,4")
    ap.add_argument("--smpv2", default="0,1")
    ap.add_argument("--label", default="exe")
    args = ap.parse_args()
    for threads in [int(t) for t in args.threads.split(",")]:
        for smpv2 in [int(v) for v in args.smpv2.split(",")]:
            failures, exact, seconds, first_bad = run_config(args.exe, threads, smpv2, args.depth, args.runs)
            print(f"{args.label}\t{threads}\t{smpv2}\t{args.depth}\t{args.runs}\t{failures}\t{exact}\t{seconds:.1f}"
                  + (f"\tfirst miss: {first_bad}" if first_bad else ""), flush=True)


main()
