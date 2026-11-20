#!/usr/bin/env python3
"""o_run.py: one O-run (depth 12, S14, Threads 1, Hash 16). Fresh engine.

Usage: o_run.py <exe> <switch: none|true|false> <raw> <meta> <fens>
Writes the engine's raw stdout to <raw> and a .meta beside it.
Prints one "n nodes" row per position to stdout.
STOP on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import subprocess
import sys

S14 = [
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

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def main():
    exe, switch, raw_path, meta_path, fens_path = sys.argv[1:6]
    if switch not in ("none", "true", "false"):
        sys.exit(f"STOP: switch must be none, true or false, got {switch}")
    fens = [ln.strip() for ln in open(fens_path, encoding="utf-8") if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
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
    option_lines = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        lines = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit("STOP: engine closed its output")
            line = line.rstrip("\n")
            raw.write(line + "\n")
            raw.flush()
            for bad in BAD:
                if bad in line:
                    sys.exit(f"STOP: {line}")
            lines.append(line)
            if done(line):
                return lines

    send("uci")
    uci_lines = read_until(lambda line: line == "uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
    send("isready")
    read_until(lambda line: line == "readyok")

    options = list(S14) + [("Threads", "1"), ("Hash", "16")]
    if switch != "none":
        options.append(("IdeaS13", switch))
    for name, value in options:
        command = f"setoption name {name} value {value}"
        option_lines.append(command)
        send(command)
        send("isready")
        read_until(lambda line: line == "readyok")

    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write("options:\n")
        for command in option_lines:
            meta.write(command + "\n")
        meta.write("per position: ucinewgame, isready, position fen <fen>, isready, go depth 12\n")

    total = 0
    for index, fen in enumerate(fens, 1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line == "readyok")
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line == "readyok")
        send("go depth 12")
        got = read_until(lambda line: line.startswith("bestmove"))
        info = [line for line in got if line.startswith("info ")]
        if not info or " nodes " not in info[-1]:
            sys.exit(f"STOP: position {index} last info line has no nodes: {info[-1] if info else 'none'}")
        parts = info[-1].split()
        nodes = int(parts[parts.index("nodes") + 1])
        total += nodes
        print(f"{index}\t{nodes}", flush=True)
    print(f"SUM\t{total}", flush=True)
    send("quit")
    proc.wait(timeout=30)
    raw.close()


if __name__ == "__main__":
    main()
