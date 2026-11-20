#!/usr/bin/env python3
"""Depth-12 node harness for the Grok swarm 2 O runs.

Usage:
  python3 o_run.py EXE RAW NODES META FENS [SWITCH true|false]

Sends Threads 1, Hash 16, then the S14 options in the brief's order.
If SWITCH is given, sends setoption name SWITCH value true|false after S14.
ucinewgame + isready before every position, isready after every setoption
and after every position. Stops on unknown option, invalid value, invalid FEN,
or illegal move. Writes one "number nodes" row per position.
"""
import hashlib
import subprocess
import sys

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def main():
    if len(sys.argv) not in (6, 8):
        sys.exit(__doc__)
    exe, raw_path, nodes_path, meta_path, fens_path = sys.argv[1:6]
    switch = None
    if len(sys.argv) == 8:
        switch = (sys.argv[6], sys.argv[7])
        if switch[1] not in ("true", "false"):
            sys.exit("STOP: switch value must be true or false")

    digest = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")

    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch is not None:
        options.append(f"setoption name {switch[0]} value {switch[1]}")

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = open(raw_path, "w", encoding="utf-8")

    def send(line):
        raw.write(">> " + line + "\n")
        raw.flush()
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def fail(message):
        raw.write("STOP " + message + "\n")
        raw.flush()
        proc.kill()
        sys.exit("STOP: " + message)

    def read_until(done):
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail("engine closed stdout")
            line = line.rstrip("\n")
            raw.write(line + "\n")
            raw.flush()
            got.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    fail(line)
            if done(line):
                return got

    def isready():
        send("isready")
        read_until(lambda line: line == "readyok")

    send("uci")
    uci_lines = read_until(lambda line: line == "uciok")
    id_name = "?"
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break

    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {digest}\n")
        meta.write(f"id name {id_name}\n")
        meta.write("options\n")
        for line in options:
            meta.write(line + "\n")

    for line in options:
        send(line)
        isready()

    rows = []
    for number, fen in enumerate(fens, 1):
        send("ucinewgame")
        isready()
        send("position fen " + fen)
        isready()
        send("go depth 12")
        body = read_until(lambda line: line.startswith("bestmove"))
        info = [line for line in body if line.startswith("info ") and " nodes " in line]
        if not info:
            fail(f"no info line for position {number}")
        parts = info[-1].split()
        nodes = None
        for index, part in enumerate(parts):
            if part == "nodes" and index + 1 < len(parts):
                nodes = int(parts[index + 1])
                break
        if nodes is None:
            fail(f"no nodes field for position {number}")
        rows.append((number, nodes))

    send("quit")
    proc.wait(timeout=30)
    raw.close()
    with open(nodes_path, "w", encoding="utf-8") as out:
        for number, nodes in rows:
            out.write(f"{number} {nodes}\n")
    print(f"{len(rows)} positions -> {nodes_path}")


if __name__ == "__main__":
    main()
