#!/usr/bin/env python3
"""Measure go-depth node counts. One engine process. S14, Threads 1, Hash 16.
ucinewgame + isready before every go. isready after every setoption and position.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
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


def die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def main():
    if len(sys.argv) < 5 or (len(sys.argv) - 5) % 2 != 0:
        die("usage: measure_set.py EXE FENS DEPTH RAW [Name Value ...]")
    exe, fen_path, depth_s, raw_path = sys.argv[1:5]
    depth = int(depth_s)
    extra = list(zip(sys.argv[5::2], sys.argv[6::2]))
    options = [("Threads", "1"), ("Hash", "16")] + S14 + extra

    with open(fen_path, "r", encoding="utf-8") as handle:
        fens = []
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fens.append(" ".join(line.split()[:6]))

    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    raw = []
    option_lines = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        raw.append(">> " + line)

    def read_until(ok):
        while True:
            line = proc.stdout.readline()
            if line == "":
                die("engine closed stdout")
            line = line.rstrip("\n")
            raw.append(line)
            low = line.lower()
            if (
                "unknown option" in low
                or "invalid value" in low
                or "invalid fen" in low
                or "illegal move" in low
            ):
                die("STOP " + line)
            if ok(line):
                return line

    send("uci")
    read_until(lambda line: line == "uciok")
    id_name = ""
    for line in raw:
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    if not id_name:
        die("no id name")

    for name, value in options:
        sent = f"setoption name {name} value {value}"
        option_lines.append(sent)
        send(sent)
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
        send(f"go depth {depth}")
        read_until(lambda line: line.startswith("bestmove "))
        nodes = None
        best = None
        for line in reversed(raw):
            if best is None and line.startswith("bestmove "):
                best = line.split()[1]
            if line.startswith("info depth ") and " nodes " in line:
                parts = line.split()
                nodes = int(parts[parts.index("nodes") + 1])
                break
        if nodes is None or best is None:
            die(f"no nodes for position {index}")
        rows.append((index, nodes, best, fen))
        if index % 50 == 0:
            sys.stderr.write(f"done {index}/{len(fens)}\n")

    send("quit")
    proc.wait(timeout=30)

    with open(raw_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(raw) + "\n")
    rows_path = raw_path + ".rows"
    with open(rows_path, "w", encoding="utf-8") as handle:
        for index, nodes, best, fen in rows:
            handle.write(f"{index}\t{nodes}\t{best}\t{fen}\n")
    meta_path = raw_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as handle:
        handle.write(f"exe {exe}\n")
        handle.write(f"sha256 {sha}\n")
        handle.write(f"id name {id_name}\n")
        handle.write(f"depth {depth}\n")
        handle.write(f"fens {fen_path}\n")
        handle.write(f"positions {len(rows)}\n")
        for line in option_lines:
            handle.write(line + "\n")
    total = sum(nodes for _, nodes, _, _ in rows)
    first = " ".join(str(nodes) for _, nodes, _, _ in rows[:3])
    sys.stdout.write(f"positions {len(rows)} sum {total} first {first}\n")


if __name__ == "__main__":
    main()
