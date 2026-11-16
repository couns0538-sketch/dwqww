#!/usr/bin/env python3
"""run_pv.py EXE FENS OUTJSONL [DEPTH]

Runs one search per FEN at DEPTH with the S14 settings, Threads 1, Hash 16.
Keeps every info line the engine sent, so the raw record is complete.
One engine process per position (fresh, so no transposition carry-over).
"""
import json
import subprocess
import sys
import time

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]


def run_one(exe, fen, depth):
    p = subprocess.Popen(exe, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []

    def send(cmd):
        p.stdin.write(cmd + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "uciok":
            break
    send("setoption name Threads value 1")
    send("isready")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "readyok":
            break
    send("setoption name Hash value 16")
    send("isready")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "readyok":
            break
    for name, val in S14:
        send(f"setoption name {name} value {val}")
    send("isready")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "readyok":
            break
    send("ucinewgame")
    send("isready")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "readyok":
            break
    send(f"position fen {fen}")
    send("isready")
    for line in p.stdout:
        lines.append(line.rstrip("\n"))
        if line.strip() == "readyok":
            break
    send(f"go depth {depth}")
    best = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        lines.append(line.rstrip("\n"))
        if line.startswith("bestmove"):
            best = line.strip()
            break
    send("quit")
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines, best


def main():
    exe, fenfile, outfile = sys.argv[1], sys.argv[2], sys.argv[3]
    depth = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    fens = [l.strip() for l in open(fenfile) if l.strip() and not l.startswith("#")]
    with open(outfile, "w") as out:
        for i, fen in enumerate(fens):
            t0 = time.monotonic()
            lines, best = run_one(exe, fen, depth)
            dt = time.monotonic() - t0
            rec = {"i": i, "fen": fen, "depth": depth, "bestmove": best,
                   "secs": round(dt, 3), "lines": lines}
            out.write(json.dumps(rec) + "\n")
            out.flush()
            if i % 25 == 0:
                print(f"{i}/{len(fens)} {fen} -> {best} ({dt:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
