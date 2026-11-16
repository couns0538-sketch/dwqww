#!/usr/bin/env python3
"""deepseek5 job3 Part 2: movetime reserve vs Move Overhead; Threads 4 wtime lines; under-load lines;
engine-reported `time` recorded beside measured elapsed (largest difference per line)."""
import chess
import json
import statistics
import subprocess
import sys
import time

ENGINE = "/tmp/ds13_base/build/forge"
EPD = "/tmp/glmflash/UHO_Lichess_4852_v1.epd"
N = 300

def run_line(label, go_line, positions, threads=1, overhead=None, load_procs=0):
    load = []
    for _ in range(load_procs):
        load.append(subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1))
    for lp in load:
        lp.stdin.write("uci\n"); lp.stdin.write("setoption name Threads value 1\n")
        lp.stdin.write("setoption name Hash value 16\n")
        lp.stdin.write("setoption name OwnBook value false\n")
        lp.stdin.write("isready\n")
        lp.stdin.write(f"position fen {positions[0]}\n")
        lp.stdin.write("go infinite\n")
        lp.stdin.flush()
    p = subprocess.Popen([ENGINE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    def send(s):
        p.stdin.write(s + "\n"); p.stdin.flush()
    def rd():
        return p.stdout.readline()
    send("uci")
    while not rd().startswith("uciok"):
        pass
    send(f"setoption name Threads value {threads}")
    send("setoption name Hash value 16")
    send("setoption name OwnBook value false")
    if overhead is not None:
        send(f"setoption name Move Overhead value {overhead}")
    send("isready")
    while not rd().startswith("readyok"):
        pass
    elapsed = []; reported = []; illegal = 0; missing = 0
    for fen in positions:
        send("ucinewgame"); send("isready")
        while not rd().startswith("readyok"):
            pass
        send(f"position fen {fen}")
        send(go_line)
        t0 = time.monotonic_ns()
        best = None; rep = None
        while True:
            line = rd()
            if not line:
                missing += 1; break
            if line.startswith("info") and " time " in line:
                t = line.split()
                try:
                    rep = int(t[t.index("time") + 1])
                except (ValueError, IndexError):
                    pass
            if line.startswith("bestmove"):
                t1 = time.monotonic_ns()
                parts = line.split()
                best = parts[1] if len(parts) > 1 else None
                break
        elapsed.append((t1 - t0) / 1e6 if best is not None else None)
        reported.append(rep)
        if best is not None:
            board = chess.Board(); board.set_fen(fen)
            try:
                if chess.Move.from_uci(best) not in board.legal_moves:
                    illegal += 1
            except Exception:
                illegal += 1
        else:
            illegal += 1
    send("quit"); p.wait(timeout=15)
    for lp in load:
        try:
            lp.stdin.write("stop\nquit\n"); lp.stdin.flush(); lp.wait(timeout=5)
        except Exception:
            lp.kill()
    vals = sorted(e for e in elapsed if e is not None)
    diffs = [abs(e - r) for e, r in zip(vals, [r for r, e0 in zip(reported, elapsed) if e0 is not None]) if r is not None]
    n = len(vals)
    t = None
    if go_line.startswith("go movetime"):
        t = int(go_line.split()[2])
    elif "wtime" in go_line:
        t = int(go_line.split()[2])
    res = {"label": label, "n": n, "illegal": illegal, "missing": missing,
           "median_ms": statistics.median(vals) if n else None,
           "p95_ms": vals[int(0.95 * (n - 1))] if n else None,
           "max_ms": vals[-1] if n else None,
           "over_T": (sum(1 for v in vals if v > t) if t is not None else None),
           "over_Tm10": (sum(1 for v in vals if v > t - 10) if t is not None else None),
           "max_diff_reported_vs_measured": max(diffs) if diffs else None}
    print(json.dumps(res), flush=True)
    return res

def main():
    positions = [l.strip() for l in open(EPD, encoding="utf-8", errors="replace")][:N]
    out = {}
    # 2a: movetime reserve vs Move Overhead
    for ov in (0, 30):
        for m in (10, 50, 200):
            out[f"2a_ov{ov}_mt{m}"] = run_line(f"movetime {m} overhead {ov}", f"go movetime {m}", positions, overhead=ov)
    # 2b: Threads 4, six wtime lines
    for T in (20, 50, 100, 300, 1000, 5000):
        out[f"2b_t4_T{T}"] = run_line(f"T4 wtime {T}", f"go wtime {T} btime {T} winc 0 binc 0", positions, threads=4)
    # 2c: under load (4 extra infinite searches on 4 cores), floor + T=20/50/100
    out["2c_floor_load"] = run_line("depth1 under load", "go depth 1", positions, load_procs=4)
    for T in (20, 50, 100):
        out[f"2c_T{T}_load"] = run_line(f"T{T} under load", f"go wtime {T} btime {T} winc 0 binc 0", positions, load_procs=4)
    json.dump(out, open("/tmp/glmflash/ds5_part2.json", "w"), indent=1)

if __name__ == "__main__":
    main()
