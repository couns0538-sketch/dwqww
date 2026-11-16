#!/usr/bin/env python3
"""kimi5 job1, extra proof for A1: `movetime 50` with Move Overhead 10 vs 0.
TIME_MODEL says hard = movetime - overhead (search.cpp:2191), so the median elapsed must
move ~10 ms between the two runs. 60 positions each; writes k5_overhead_probe.json."""
import json
import statistics
import subprocess
import time

ENGINE = "/tmp/kimi5/build/forge"
FENS = "/tmp/kimi5/k5_worst20.fens" + ""  # 20 dense positions, cycled 3x -> 60


def run(overhead, positions, input_log):
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        input_log.write(s + "\n")
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send(f"setoption name Move Overhead value {overhead}")
    send("isready")
    while not p.stdout.readline().startswith("readyok"):
        pass
    vals = []
    for fen in positions:
        send("ucinewgame")
        send("isready")
        while not p.stdout.readline().startswith("readyok"):
            pass
        send(f"position fen {fen}")
        send("go movetime 50")
        t0 = time.monotonic_ns()
        while True:
            line = p.stdout.readline()
            if line.startswith("bestmove"):
                vals.append((time.monotonic_ns() - t0) / 1e6)
                break
    send("quit")
    p.wait(timeout=20)
    return {"overhead": overhead, "n": len(vals), "median_ms": statistics.median(vals),
            "min_ms": min(vals), "max_ms": max(vals)}


def main():
    base = [l.strip() for l in open(FENS) if l.strip()]
    positions = base * 3
    out = {}
    with open("k5_overhead_probe_input.log", "w") as log:
        for overhead in (10, 0):
            out[f"overhead_{overhead}"] = run(overhead, positions, log)
            print(json.dumps(out[f"overhead_{overhead}"]), flush=True)
    json.dump(out, open("k5_overhead_probe.json", "w"), indent=1)


if __name__ == "__main__":
    main()
