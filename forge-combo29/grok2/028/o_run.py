#!/usr/bin/env python3
"""o_run.py EXE RAW META FENS [true|false]

One engine process. S14, Threads 1 and Hash 16 are sent before the positions.
The optional last argument is the IdeaK4 value. Every setoption and every
position is followed by isready, and every line is read up to readyok.
Stops on unknown option, invalid value, invalid FEN or illegal move.
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

STOP_MARKS = ("unknown option", "invalid value", "invalid fen", "illegal move")


def die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(1)


def main():
    if len(sys.argv) not in (5, 6):
        die("usage: o_run.py EXE RAW META FENS [true|false]")
    exe, raw_path, meta_path, fens_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) == 6 else None
    if switch not in (None, "true", "false"):
        die("switch must be true or false")
    with open(fens_path, encoding="utf-8") as f:
        fens = [line.strip() for line in f if line.strip()]
    if len(fens) != 200:
        die(f"expected 200 fens, got {len(fens)}")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    options = [("Threads", "1"), ("Hash", "16")] + S14
    if switch is not None:
        options.append(("IdeaK4", switch))
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    engine_lines = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        while True:
            line = proc.stdout.readline()
            if line == "":
                die("STOP: engine closed stdout")
            engine_lines.append(line)
            low = line.lower()
            for mark in STOP_MARKS:
                if mark in low:
                    open(raw_path, "w", encoding="utf-8").write("".join(engine_lines))
                    die(f"STOP: {line.strip()}")
            if done(line):
                return line

    send("uci")
    read_until(lambda line: line.startswith("uciok"))
    id_name = ""
    for line in engine_lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):].rstrip("\n")
            break
    if not id_name:
        die("STOP: no id name")
    for name, value in options:
        send(f"setoption name {name} value {value}")
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send(f"position fen {fen}")
        send("isready")
        read_until(lambda line: line.startswith("readyok"))
        send("go depth 12")
        read_until(lambda line: line.startswith("bestmove "))
        if index % 25 == 0:
            sys.stderr.write(f"position {index}\n")
    send("quit")
    proc.stdin.close()
    rest = proc.stdout.read()
    if rest:
        engine_lines.append(rest)
    code = proc.wait(timeout=30)
    with open(raw_path, "w", encoding="utf-8") as out:
        out.write("".join(engine_lines))
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe: {exe}\n")
        meta.write(f"sha256: {sha}\n")
        meta.write(f"id name: {id_name}\n")
        meta.write("option lines sent:\n")
        for name, value in options:
            meta.write(f"setoption name {name} value {value}\n")
        meta.write(f"engine exit: {code}\n")
    print(f"wrote {raw_path} lines {len(engine_lines)} exit {code}")


if __name__ == "__main__":
    main()
