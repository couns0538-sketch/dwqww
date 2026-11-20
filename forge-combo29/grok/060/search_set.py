#!/usr/bin/env python3
"""Fixed-depth search of a FEN list. S14, Threads 1, Hash 16.

Usage: search_set.py EXE FENS DEPTH OUTPREFIX [true|false|none]
none does not send IdeaS24 (the plain engine does not know it).
Writes OUTPREFIX.tsv, OUTPREFIX.raw, OUTPREFIX.meta.
Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import os
import subprocess
import sys

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
    ("Threads", "1"),
    ("Hash", "16"),
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fens(path):
    fens = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            fens.append(text.split(";")[0].strip())
    return fens


def nodes_of(info_line):
    parts = info_line.split()
    if "nodes" not in parts:
        return None
    index = parts.index("nodes")
    return int(parts[index + 1])


def depth_of(info_line):
    parts = info_line.split()
    if "depth" not in parts:
        return None
    index = parts.index("depth")
    return int(parts[index + 1])


def main():
    if len(sys.argv) != 6:
        sys.stderr.write("usage: search_set.py EXE FENS DEPTH OUTPREFIX SWITCH\n")
        sys.exit(2)
    exe = os.path.abspath(sys.argv[1])
    fen_path = sys.argv[2]
    depth = int(sys.argv[3])
    prefix = sys.argv[4]
    switch = sys.argv[5]
    if switch not in ("true", "false", "none"):
        sys.stderr.write("switch must be true, false, or none\n")
        sys.exit(2)
    fens = load_fens(fen_path)
    options = list(S14)
    if switch != "none":
        options.append(("IdeaS24", switch))
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []

    def send(line):
        raw.append(">> " + line)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        got = []
        while True:
            line = proc.stdout.readline()
            if line == "":
                raw.append("ENGINE CLOSED")
                proc.kill()
                sys.stderr.write("engine closed\n")
                sys.exit(2)
            line = line.rstrip("\r\n")
            raw.append(line)
            got.append(line)
            if any(bad in line for bad in STOP):
                sys.stderr.write("STOP " + line + "\n")
                proc.kill()
                sys.exit(2)
            if done(line):
                return got

    send("uci")
    uci_lines = read_until(lambda line: line == "uciok")
    id_name = ""
    for line in uci_lines:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    option_lines = []
    for name, value in options:
        command = "setoption name " + name + " value " + value
        option_lines.append(command)
        send(command)
        send("isready")
        read_until(lambda line: line == "readyok")
    rows = []
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda line: line == "readyok")
        send("go depth " + str(depth))
        lines = read_until(lambda line: line.startswith("bestmove "))
        info = [line for line in lines if line.startswith("info depth ")]
        if not info:
            sys.stderr.write("no info for position " + str(index) + "\n")
            proc.kill()
            sys.exit(2)
        last = info[-1]
        best = lines[-1].split()
        bestmove = best[1] if len(best) > 1 else ""
        rows.append((index, nodes_of(last), depth_of(last), bestmove))
        if index % 50 == 0:
            sys.stderr.write("positions " + str(index) + "\n")
    send("quit")
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    digest = sha256(exe)
    with open(prefix + ".tsv", "w", encoding="utf-8") as handle:
        handle.write("index\tnodes\tdepth\tbestmove\n")
        for index, nodes, got_depth, bestmove in rows:
            handle.write(f"{index}\t{nodes}\t{got_depth}\t{bestmove}\n")
    with open(prefix + ".raw", "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw) + "\n")
    with open(prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write("exe " + exe + "\n")
        handle.write("sha256 " + digest + "\n")
        handle.write("id_name " + id_name + "\n")
        handle.write("options\n")
        for command in option_lines:
            handle.write(command + "\n")
        handle.write("fens " + os.path.abspath(fen_path) + "\n")
        handle.write("depth " + str(depth) + "\n")
        handle.write("switch " + switch + "\n")
        handle.write("rows " + str(len(rows)) + "\n")
    print("rows", len(rows), flush=True)


if __name__ == "__main__":
    main()
