#!/usr/bin/env python3
"""kimi5 job3: fixed-depth searches over UHO positions, one switch config per run.
One engine process per run. Mode "fresh": ucinewgame + isready before EVERY search
(empty hash+history per search). Mode "repeat": ucinewgame+isready only once at the
start, tables carry over from search to search as in a game. Blocking line reads only
(job-2 pattern). Every command mirrored into an input log (proof the option arrived).
Per search: pos, config, depth, nodes (engine's own per-search k5ctr nodes), the 17
counter DELTAS (cumulative k5ctr diffed against the previous search), bestmove
(legality-checked), engine's own last `time`, wall ms.
Usage: k5_j3.py <engine> <positions.fens> <config> <depth> <fresh|repeat> [npos]
Writes k5_j3_<config>_d<depth>_<mode>.json and ..._input.log in the CWD."""
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

SWITCHES = ["LmrDeeperShallower", "ThreatHistory", "NullThreatVerify", "NullSeeVeto",
            "ContHist4PlyRead", "AspCappedReopen", "HindsightDepth", "SoundMatePruning"]
CONFIGS = {
    "off": [],
    "lmrs": ["LmrDeeperShallower"],
    "thr": ["ThreatHistory"],
    "ntv": ["NullThreatVerify"],
    "nsv": ["NullSeeVeto"],
    "ch4": ["ContHist4PlyRead"],
    "acr": ["AspCappedReopen"],
    "hd": ["HindsightDepth"],
    "smp": ["SoundMatePruning"],
    "six": ["LmrDeeperShallower", "ThreatHistory", "NullThreatVerify", "NullSeeVeto",
            "ContHist4PlyRead", "AspCappedReopen"],
}
CTR_KEYS = ["lmrds_deeper", "lmrds_shallower", "thr_reads", "thr_nonzero", "ntv_gates",
            "ntv_ver_cut", "ntv_ver_fail", "nsv_calls", "nsv_vetoes", "ch4_adds",
            "acr_low", "acr_high", "hd_considered", "hd_minus", "hd_plus",
            "hd_ttblocked", "smp_arm_moves"]


def main():
    positions = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    boards = [chess.Board(f) for f in positions]
    setopts = CONFIGS[CONFIG]
    tag = f"{CONFIG}_d{DEPTH}_{MODE}"
    input_log = open(f"k5_j3_{tag}_input.log", "w")
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
    for sw in setopts:
        send(f"setoption name {sw} value true")
    send("isready")
    wait_prefix("readyok")
    if MODE == "repeat":
        send("ucinewgame")
        send("isready")
        wait_prefix("readyok")

    records = []
    illegal = 0
    failures = 0
    prev_ctr = {k: 0 for k in CTR_KEYS}
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
            elif line.startswith("info string k5ctr "):
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
                ctr = {k: int(parts[parts.index(k) + 1]) for k in CTR_KEYS}
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
        deltas = {k: ctr[k] - prev_ctr[k] for k in CTR_KEYS} if ctr is not None else {}
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
    with open(f"k5_j3_{tag}.json", "w") as f:
        json.dump({"config": CONFIG, "setopts": setopts, "depth": DEPTH, "mode": MODE,
                   "n_positions": len(positions), "illegal": illegal,
                   "failures": failures, "records": records}, f)
    print(f"{tag}: {len(records)} searches, illegal={illegal}, failures={failures}")


if __name__ == "__main__":
    main()
