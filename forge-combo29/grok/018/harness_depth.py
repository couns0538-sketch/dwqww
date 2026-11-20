#!/usr/bin/env python3
"""Depth search of a FEN/EPD list. Stops on unknown option, invalid value, invalid FEN, illegal move.

Usage: harness_depth.py EXE FENFILE DEPTH OUT_PREFIX [LIMIT] [extra setoption lines...]
S14, then Threads 1, then Hash 16, then any extra lines. isready after every setoption and position.
ucinewgame + isready before every go. OUT_PREFIX.raw is the engine text, .tsv the parsed rows,
.meta the exe, sha256, id name, and options.
"""
import hashlib
import subprocess
import sys

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
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def fail(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def main():
    if len(sys.argv) < 5:
        fail("usage: harness_depth.py EXE FENFILE DEPTH OUT_PREFIX [LIMIT] [setoption ...]")
    exe, fenfile, depth_s, prefix = sys.argv[1:5]
    rest = sys.argv[5:]
    limit = 0
    extra = []
    if rest:
        if rest[0].isdigit():
            limit = int(rest[0])
            extra = rest[1:]
        else:
            extra = rest
    depth = int(depth_s)
    options = S14 + extra
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    fens = []
    for line in open(fenfile, encoding="utf-8"):
        parts = line.split()
        if len(parts) < 6:
            continue
        fens.append(" ".join(parts[:6]))
        if limit and len(fens) >= limit:
            break
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = open(prefix + ".raw", "w", encoding="utf-8")

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker):
        lines = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail("engine closed waiting for " + marker)
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            raw.flush()
            lines.append(line)
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    fail("STOP " + line)
            if line.startswith(marker) or line == marker:
                return lines
        return lines

    send("uci")
    uci_lines = read_until("uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    for opt in options:
        send(opt)
        send("isready")
        read_until("readyok")
    rows = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until("readyok")
        send("position fen " + fen)
        send("isready")
        read_until("readyok")
        send("go depth " + str(depth))
        nodes = None
        best = None
        while True:
            line = proc.stdout.readline()
            if line == "":
                fail("engine closed during search " + str(index))
            line = line.rstrip("\r\n")
            raw.write(line + "\n")
            raw.flush()
            low = line.lower()
            for bad in BAD:
                if bad.lower() in low:
                    fail("STOP " + line)
            if line.startswith("info depth "):
                parts = line.split()
                if "nodes" in parts:
                    nodes = int(parts[parts.index("nodes") + 1])
            if line.startswith("bestmove "):
                best = line.split()[1]
                break
        if nodes is None:
            fail("no nodes for position " + str(index))
        rows.append((index, nodes, best, fen))
    send("quit")
    proc.wait(timeout=30)
    raw.close()
    total = 0
    with open(prefix + ".tsv", "w", encoding="utf-8") as out:
        out.write("index\tnodes\tbestmove\tfen\n")
        for index, nodes, best, fen in rows:
            total += nodes
            out.write(f"{index}\t{nodes}\t{best}\t{fen}\n")
        out.write(f"SUM\t{total}\t\t\n")
    with open(prefix + ".meta", "w", encoding="utf-8") as meta:
        meta.write("exe " + exe + "\n")
        meta.write("sha256 " + sha + "\n")
        meta.write("id name " + id_name + "\n")
        meta.write("fenfile " + fenfile + "\n")
        meta.write("depth " + str(depth) + "\n")
        meta.write("positions " + str(len(rows)) + "\n")
        for opt in options:
            meta.write("option " + opt + "\n")
    sys.stdout.write(f"positions {len(rows)} sum {total}\n")


if __name__ == "__main__":
    main()
