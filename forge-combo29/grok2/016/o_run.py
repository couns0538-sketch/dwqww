#!/usr/bin/env python3
"""Depth-12 O harness. One engine process. Options before every position.

Usage: o_run.py EXE FENS RAW ROWS META [SWITCH VALUE]
SWITCH is the UCI name (IdeaS32). VALUE is true or false.
Omit both for exe B, which does not have the switch.
"""
import hashlib
import subprocess
import sys

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")
S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
    ("LmrQuietBase", "93"),
    ("LmrQuietDivisor", "205"),
    ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"),
    ("LmrHistoryDivisor", "5643"),
    ("NullMoveBase", "5"),
    ("LmpBase", "8"),
    ("HistoryPruneMultiplier", "2220"),
    ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"),
    ("HistoryBonusMax", "2212"),
    ("SingularDepth", "6"),
    ("IirDepth", "2"),
    ("NonPawnCorrection", "true"),
]


def stop(msg):
    sys.exit("STOP: " + msg)


def main():
    if len(sys.argv) not in (6, 8):
        stop("usage: o_run.py EXE FENS RAW ROWS META [SWITCH VALUE]")
    exe, fens, raw_path, rows_path, meta_path = sys.argv[1:6]
    extra = []
    if len(sys.argv) == 8:
        extra.append((sys.argv[6], sys.argv[7]))
    options = S14 + extra
    with open(fens, encoding="utf-8") as f:
        positions = [line.strip() for line in f if line.strip()]
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = open(raw_path, "w", encoding="utf-8")
    id_name = ""

    def send(line):
        raw.write(">> " + line + "\n")
        raw.flush()
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(marker, limit=200000):
        for _ in range(limit):
            line = proc.stdout.readline()
            if line == "":
                stop("engine closed stdout")
            raw.write(line)
            raw.flush()
            for bad in BAD:
                if bad in line:
                    stop(line.rstrip("\n"))
            if marker(line):
                return line
        stop("no marker from engine")

    send("uci")
    def on_uci(line):
        nonlocal id_name
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\n")
        return line.startswith("uciok")
    read_until(on_uci)

    rows = []
    for n, fen in enumerate(positions, start=1):
        for name, value in options:
            send(f"setoption name {name} value {value}")
            send("isready")
            read_until(lambda line: line.startswith("readyok"))
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send("position fen " + fen)
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send("go depth 12")
        infos = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                stop("engine closed stdout during go")
            raw.write(line)
            raw.flush()
            for bad in BAD:
                if bad in line:
                    stop(line.rstrip("\n"))
            if line.startswith("info "):
                infos.append(line.rstrip("\n"))
            if line.startswith("bestmove"):
                break
        node_line = ""
        for info in reversed(infos):
            if " nodes " in info:
                node_line = info
                break
        if node_line == "":
            stop(f"position {n} has no info nodes line")
        nodes = node_line.split(" nodes ", 1)[1].split()[0]
        if not nodes.isdigit():
            stop(f"position {n} nodes not an integer: {nodes}")
        rows.append((n, int(nodes)))
        if n % 20 == 0:
            print(f"position {n}", file=sys.stderr, flush=True)
    send("quit")
    proc.wait(timeout=30)
    raw.close()
    with open(rows_path, "w", encoding="utf-8") as o:
        for n, nodes in rows:
            o.write(f"{n}\t{nodes}\n")
    with open(meta_path, "w", encoding="utf-8") as m:
        m.write(f"exe: {exe}\n")
        m.write(f"sha256: {sha}\n")
        m.write(f"id name: {id_name}\n")
        m.write("options:\n")
        for name, value in options:
            m.write(f"setoption name {name} value {value}\n")
        m.write(f"positions: {len(rows)}\n")
    print(f"rows {len(rows)} sum {sum(v for _, v in rows)}", file=sys.stderr)


if __name__ == "__main__":
    main()
