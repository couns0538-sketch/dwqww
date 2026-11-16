#!/usr/bin/env python3
"""deepseek5 job1 Part A: does the engine ever use more time than it has?
One engine process; monotonic clock around the pipes; 300 UHO positions."""
import chess
import json
import statistics
import subprocess
import sys
import time

ENGINE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ds13_base/build/forge"
EPD = "/tmp/glmflash/UHO_Lichess_4852_v1.epd"
N = 300

def one_process(label, go_line, positions, wrapper=None, out_key=""):
    """Run one go_line over all positions in a single fresh engine process."""
    cmd = [wrapper, ENGINE] if wrapper else [ENGINE]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()
    def readline():
        return p.stdout.readline()
    send("uci")
    while True:
        if readline().startswith("uciok"):
            break
    send("setoption name Threads value 1")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    send("isready")
    while True:
        if readline().startswith("readyok"):
            break
    elapsed = []
    illegal = 0
    missing = 0
    for fen in positions:
        send("ucinewgame")
        send("isready")
        while True:
            if readline().startswith("readyok"):
                break
        send(f"position fen {fen}")
        send(go_line)
        t0 = time.monotonic_ns()
        best = None
        while True:
            line = readline()
            if not line:
                missing += 1
                break
            if line.startswith("bestmove"):
                t1 = time.monotonic_ns()
                parts = line.split()
                best = parts[1] if len(parts) > 1 else None
                break
        elapsed.append((t1 - t0) / 1e6 if best is not None else None)
        if best is not None:
            board = chess.Board()
            board.set_fen(fen)
            try:
                mv = chess.Move.from_uci(best)
                if mv not in board.legal_moves:
                    illegal += 1
            except Exception:
                illegal += 1
        else:
            illegal += 1
    send("quit")
    p.wait(timeout=15)
    vals = sorted(e for e in elapsed if e is not None)
    n = len(vals)
    res = {
        "label": label, "n": n, "illegal_or_missing": illegal,
        "median_ms": statistics.median(vals) if n else None,
        "p95_ms": vals[int(0.95 * (n - 1))] if n else None,
        "max_ms": vals[-1] if n else None,
        "over_T": 0, "over_Tm10": 0,
    }
    if go_line.startswith("go movetime"):
        m = int(go_line.split()[2])
        res["over_T"] = sum(1 for v in vals if v > m)
        res["over_Tm10"] = sum(1 for v in vals if v > m - 10)
    else:
        t = int(go_line.split()[2])
        res["over_T"] = sum(1 for v in vals if v > t)
        res["over_Tm10"] = sum(1 for v in vals if v > t - 10)
    print(json.dumps(res), flush=True)
    return res

def main():
    positions = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")][:N]
    lines = [
        "go wtime 20 btime 20 winc 0 binc 0",
        "go wtime 50 btime 50 winc 0 binc 0",
        "go wtime 100 btime 100 winc 0 binc 0",
        "go wtime 300 btime 300 winc 0 binc 0",
        "go wtime 1000 btime 1000 winc 0 binc 0",
        "go wtime 5000 btime 5000 winc 0 binc 0",
        "go wtime 50 btime 50 winc 0 binc 0 movestogo 1",
        "go wtime 300 btime 300 winc 0 binc 0 movestogo 1",
        "go movetime 10",
        "go movetime 50",
        "go movetime 200",
    ]
    out = {}
    out["control1_depth1"] = one_process("control1 depth1", "go depth 1", positions)
    for ln in lines:
        out[ln] = one_process(ln, ln, positions)
    print(json.dumps({"__PARTA__": out}), flush=True)
    json.dump(out, open("/tmp/glmflash/ds5_part_a.json", "w"), indent=1)

if __name__ == "__main__":
    main()
