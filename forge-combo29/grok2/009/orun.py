#!/usr/bin/env python3
"""One O-run: S14, Threads 1, Hash 16, depth 12 on each FEN.

Usage: python3 orun.py <exe> <fens> <out> <meta> [switch]
switch is omitted, or "IdeaS13=false", or "IdeaS13=true".
Sends isready after every setoption and every position. Stops on a refusal.
"""
import hashlib
import subprocess
import sys

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
    "setoption name LmrQuietBase value 93",
    "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13",
    "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643",
    "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8",
    "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24",
    "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212",
    "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2",
    "setoption name NonPawnCorrection value true",
]


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) not in (5, 6):
        sys.exit("usage: orun.py <exe> <fens> <out> <meta> [Switch=true|false]")
    exe, fens_path, out_path, meta_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) == 6 else None
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch is not None:
        name, value = switch.split("=", 1)
        if value not in ("true", "false"):
            sys.exit(f"STOP: switch value must be true or false, got {value}")
        options.append(f"setoption name {name} value {value}")

    fens = []
    with open(fens_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                fens.append(line)
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")

    exe_sha = file_sha256(exe)
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines = []
    id_name = ""

    def fail(msg):
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        sys.exit(msg)

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail("STOP: engine closed stdout")
            line = line.rstrip("\n")
            lines.append(line)
            low = line.lower()
            for token in STOP:
                if token.lower() in low:
                    fail(f"STOP: {line}")
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            if pred(line):
                return line

    send("uci")
    read_until(lambda line: line == "uciok")
    for option in options:
        send(option)
        send("isready")
        read_until(lambda line: line == "readyok")
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line == "readyok")
        send("go depth 12")
        read_until(lambda line: line.startswith("bestmove "))
        if index % 20 == 0:
            print(f"position {index}", flush=True)
    send("quit")
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line.rstrip("\n"))
    rc = proc.wait(timeout=30)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"exe: {exe}\n")
        f.write(f"sha256: {exe_sha}\n")
        f.write(f"id name: {id_name}\n")
        f.write("options:\n")
        for option in options:
            f.write(option + "\n")
        f.write(f"fens: {fens_path}\n")
        f.write(f"positions: {len(fens)}\n")
        f.write(f"exit: {rc}\n")
    print(f"wrote {out_path} lines {len(lines)} exit {rc}")


if __name__ == "__main__":
    main()
