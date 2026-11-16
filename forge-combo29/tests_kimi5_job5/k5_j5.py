#!/usr/bin/env python3
"""kimi5 job5: fixed-depth searches over a position set, one config per run.
Adapted from k5_j4.py. One engine process per run; ucinewgame + isready before EVERY
search (empty table per search). The exe is proven: a .meta file beside every result
carries the exe path, its sha256 and the `id name` from the uci handshake. Every command
is mirrored into an input log. After the setoptions are sent, isready is awaited and the
lines are scanned: `unknown option` or `invalid value` stops the run. Nodes come from the
engine's last info line; regret counters from the `info string soundregret` line (deltas).
Usage: k5_j5.py <engine> <positions.fens> <config> <depth> <outdir> [npos]
Configs:
  none   - all defaults                       (K1)
  smp    - SoundMatePruning true              (K2)
  pv     - SoundPvArm 1                       (K3)
  chk    - SoundInCheckArm 1                  (K4)
  mat    - SoundMateAlphaArm 1                (K5)
  pvchk  - SoundPvArm 1 + SoundInCheckArm 1   (K6)
  off7   - SoundMatePruning true, three arms -1 (K7)
  cnt    - none + SoundRegretCount true       (R1)
  cntsmp - smp  + SoundRegretCount true       (R3)
  probe  - none + SoundRegretCount true + SoundRegretProbe true   (Part 3 table)
  maskNN - SoundMatePruning true + SoundStepMask NN               (Part 4)
  pvmaskNN - SoundPvArm 1 + SoundStepMask NN                      (Part 4)
  mask0  - SoundMatePruning true + SoundStepMask 0  (= K1 check)
"""
import chess
import hashlib
import json
import subprocess
import sys
import time

ENGINE = sys.argv[1]
FENS = sys.argv[2]
CONFIG = sys.argv[3]
DEPTH = int(sys.argv[4])
OUTDIR = sys.argv[5]
NPOS = int(sys.argv[6]) if len(sys.argv) > 6 else 10**9

SMP = ["setoption name SoundMatePruning value true"]
CONFIGS = {
    "none": [],
    "smp": SMP,
    "pv": ["setoption name SoundPvArm value 1"],
    "chk": ["setoption name SoundInCheckArm value 1"],
    "mat": ["setoption name SoundMateAlphaArm value 1"],
    "pvchk": ["setoption name SoundPvArm value 1", "setoption name SoundInCheckArm value 1"],
    "off7": SMP + ["setoption name SoundPvArm value -1", "setoption name SoundInCheckArm value -1",
                   "setoption name SoundMateAlphaArm value -1"],
    "cnt": ["setoption name SoundRegretCount value true"],
    "cntsmp": SMP + ["setoption name SoundRegretCount value true"],
    "probe": ["setoption name SoundRegretCount value true", "setoption name SoundRegretProbe value true"],
    "mask0": SMP + ["setoption name SoundStepMask value 0"],
}
for _nn in (1, 15, 33, 48, 51, 60, 62):
    CONFIGS[f"mask{_nn}"] = SMP + [f"setoption name SoundStepMask value {_nn}"]
    CONFIGS[f"pvmask{_nn}"] = ["setoption name SoundPvArm value 1",
                               f"setoption name SoundStepMask value {_nn}"]


def main():
    positions = [l.strip() for l in open(FENS) if l.strip()][:NPOS]
    boards = [chess.Board(f) for f in positions]
    setopts = CONFIGS[CONFIG]
    tag = f"{CONFIG}_d{DEPTH}"
    exe_sha = hashlib.sha256(open(ENGINE, "rb").read()).hexdigest()
    input_log = open(f"{OUTDIR}/k5_j5_{tag}_input.log", "w")
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

    def wait_ready_checked():
        while True:
            line = readline()
            if line == "":
                raise RuntimeError("engine closed stdout waiting for readyok")
            if "unknown option" in line or "invalid value" in line:
                raise RuntimeError(f"option refused: {line.strip()}")
            if line.startswith("readyok"):
                return

    send("uci")
    id_name = ""
    while True:
        line = readline()
        if line == "":
            raise RuntimeError("engine closed stdout waiting for uciok")
        if line.startswith("id name "):
            id_name = line[len("id name "):].strip()
        if line.startswith("uciok"):
            break
    with open(f"{OUTDIR}/k5_j5_{tag}.meta", "w") as m:
        m.write(f"exe {ENGINE}\nsha256 {exe_sha}\nid name {id_name}\n")
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    for s in setopts:
        send(s)
    send("isready")
    wait_ready_checked()

    records = []
    illegal = 0
    failures = 0
    prev_ctr = {}
    for pi, board in enumerate(boards):
        send("ucinewgame")
        send("isready")
        wait_ready_checked()
        send(f"position fen {positions[pi]}")
        send(f"go depth {DEPTH}")
        t0 = time.monotonic_ns()
        best = None
        nodes = None
        ctr = None
        while True:
            line = readline()
            if line == "":
                failures += 1
                break
            if line.startswith("info depth "):
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
            elif line.startswith("info string soundregret "):
                parts = line.split()
                kv = {}
                i = parts.index("soundregret") + 1
                while i + 1 < len(parts):
                    kv[parts[i]] = int(parts[i + 1])
                    i += 2
                ctr = kv
            elif line.startswith("bestmove"):
                parts = line.split()
                best = parts[1] if len(parts) > 1 else "0000"
                break
        wall_ms = (time.monotonic_ns() - t0) / 1e6
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
                        "wall_ms": round(wall_ms, 2), "ctr": deltas})
    send("quit")
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    input_log.close()
    with open(f"{OUTDIR}/k5_j5_{tag}.json", "w") as f:
        json.dump({"config": CONFIG, "setopts": setopts, "depth": DEPTH,
                   "n_positions": len(positions), "illegal": illegal,
                   "failures": failures, "records": records}, f)
    print(f"{tag}: {len(records)} searches, illegal={illegal}, failures={failures}")


if __name__ == "__main__":
    main()
