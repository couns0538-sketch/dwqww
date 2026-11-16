#!/usr/bin/env python3
"""kimi5 job4: fixed-depth searches over the job-3 200 UHO positions, one config per run.
Adapted from k5_j3.py: configs are named sets of setoption lines (switches AND the four
LmrDeeperShallower spin options). Mode "fresh": ucinewgame + isready before EVERY search
(empty hash+history per search). Blocking line reads only. Every command mirrored into an
input log (proof the options arrived). Per search: pos, config, depth, nodes (k5j4ctr line
when present, else the engine's last info nodes), counter DELTAS (cumulative diffed),
bestmove (legality-checked), engine's own last `time`, wall ms.
Usage: k5_j4.py <engine> <positions.fens> <config> <depth> <fresh|repeat> [npos]
Writes k5_j4_<config>_d<depth>_<mode>.json and ..._input.log in the CWD.
Configs:
  off   - nothing (all switches default off)
  on    - LmrDeeperShallower true, four tunables at defaults      (= K2 / Part 4 'both')
  k3    - on + LmrDeeperBase 100000 + LmrShallowerBase -100000    (neither can fire)
  k4a..d- on with ONE tunable changed (wiring proof)
  shal  - on + LmrDeeperBase 100000        (Part 4 'shallower only')
  deep  - on + LmrShallowerBase -100000    (Part 4 'deeper only')
  half  - on + LmrDeeperBase 20 + LmrDeeperDepthMul 1   (half margins)
  dbl   - on + LmrDeeperBase 80 + LmrDeeperDepthMul 4   (double margins)
  flat  - on + LmrShallowerBase 8 + LmrShallowerDepthMul 0 (flat shallower)
"""
import chess
import json
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
CONFIG = sys.argv[3]
DEPTH = int(sys.argv[4])
MODE = sys.argv[5]
NPOS = int(sys.argv[6]) if len(sys.argv) > 6 else 200

ON = ["setoption name LmrDeeperShallower value true"]
CONFIGS = {
    "off": [],
    "on": ON,
    "k3": ON + ["setoption name LmrDeeperBase value 100000",
                "setoption name LmrShallowerBase value -100000"],
    "k4a": ON + ["setoption name LmrDeeperBase value 20"],
    "k4b": ON + ["setoption name LmrDeeperDepthMul value 4"],
    "k4c": ON + ["setoption name LmrShallowerBase value 50"],
    "k4d": ON + ["setoption name LmrShallowerDepthMul value 3"],
    "shal": ON + ["setoption name LmrDeeperBase value 100000"],
    "deep": ON + ["setoption name LmrShallowerBase value -100000"],
    "half": ON + ["setoption name LmrDeeperBase value 20",
                  "setoption name LmrDeeperDepthMul value 1"],
    "dbl": ON + ["setoption name LmrDeeperBase value 80",
                 "setoption name LmrDeeperDepthMul value 4"],
    "flat": ON + ["setoption name LmrShallowerBase value 8",
                  "setoption name LmrShallowerDepthMul value 0"],
}


def main():
    positions = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    boards = [chess.Board(f) for f in positions]
    setopts = CONFIGS[CONFIG]
    tag = f"{CONFIG}_d{DEPTH}_{MODE}"
    input_log = open(f"k5_j4_{tag}_input.log", "w")
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        input_log.write(s + "\n")
        input_log.flush()
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def readline():
        return p.stdout.readline()

    def wait_prefix(prefix):
        while True:
            line = readline()
            if line == "":
                raise RuntimeError(f"engine closed stdout waiting for {prefix}")
            if line.startswith(prefix):
                return

    send("uci")
    wait_prefix("uciok")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    for s in setopts:
        send(s)
    send("isready")
    wait_prefix("readyok")
    if MODE == "repeat":
        send("ucinewgame")
        send("isready")
        wait_prefix("readyok")

    records = []
    illegal = 0
    failures = 0
    prev_ctr = {}
    for pi, board in enumerate(boards):
        if MODE == "fresh":
            send("ucinewgame")
            send("isready")
            wait_prefix("readyok")
        send(f"position fen {positions[pi]}")
        send(f"go depth {DEPTH}")
        t0 = time.monotonic_ns()
        best = None
        last_time = None
        ctr = None
        nodes = None
        last_info_nodes = None
        while True:
            line = readline()
            if line == "":
                failures += 1
                break
            if line.startswith("info depth "):
                parts = line.split()
                if "time" in parts:
                    last_time = int(parts[parts.index("time") + 1])
                if "nodes" in parts:
                    last_info_nodes = int(parts[parts.index("nodes") + 1])
            elif line.startswith("info string k5j4ctr "):
                parts = line.split()
                kv = {}
                i = parts.index("k5j4ctr") + 1
                while i + 1 < len(parts):
                    kv[parts[i]] = int(parts[i + 1])
                    i += 2
                nodes = kv.pop("nodes")
                ctr = kv
            elif line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else "0000"
                break
        wall_ms = (time.monotonic_ns() - t0) / 1e6
        if nodes is None:
            nodes = last_info_nodes
        if best is None or nodes is None:
            records.append({"pos": pi, "failed": True, "best": best, "ctr_seen": ctr is not None})
            continue
        try:
            mv = chess.Move.from_uci(best)
            if mv not in board.legal_moves:
                illegal += 1
        except Exception:
            illegal += 1
        deltas = {k: ctr[k] - prev_ctr.get(k, 0) for k in ctr} if ctr is not None else {}
        if ctr is not None:
            prev_ctr = ctr
        records.append({"pos": pi, "nodes": nodes, "bestmove": best,
                        "engine_time": last_time, "wall_ms": round(wall_ms, 2),
                        "ctr": deltas})
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    input_log.close()
    with open(f"k5_j4_{tag}.json", "w") as f:
        json.dump({"config": CONFIG, "setopts": setopts, "depth": DEPTH, "mode": MODE,
                   "n_positions": len(positions), "illegal": illegal,
                   "failures": failures, "records": records}, f)
    print(f"{tag}: {len(records)} searches, illegal={illegal}, failures={failures}")


if __name__ == "__main__":
    main()
