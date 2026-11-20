#!/usr/bin/env python3
"""O-run harness. One engine process. S14, Threads 1, Hash 16 before every position.

Usage: o_run.py EXE OUT.txt META.txt FENS SWITCH
SWITCH is none, false, or true. IdeaB8 is sent only for false or true.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import subprocess
import sys

STOPS = ("unknown option", "invalid value", "invalid fen", "illegal move")
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


def stop(line):
    low = line.lower()
    return any(mark in low for mark in STOPS)


def main():
    exe, out_path, meta_path, fens_path, switch = sys.argv[1:6]
    if switch not in ("none", "false", "true"):
        sys.exit("STOP: switch must be none, false, or true")
    options = list(S14)
    if switch != "none":
        options.append(("IdeaB8", switch))
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
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
    id_name = ""

    def send(line):
        assert proc.stdin is not None
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(done):
        assert proc.stdout is not None
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit("STOP: engine closed stdout")
            line = line.rstrip("\r\n")
            raw.append(line)
            if stop(line):
                open(out_path, "w", encoding="utf-8").write("\n".join(raw) + "\n")
                sys.exit("STOP: " + line)
            if done(line):
                return line

    try:
        send("uci")
        read_until(lambda line: line == "uciok")
        for line in raw:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
                break
        for index, fen in enumerate(fens, start=1):
            for name, value in options:
                send(f"setoption name {name} value {value}")
                send("isready")
                read_until(lambda line: line == "readyok")
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line == "readyok")
            send(f"position fen {fen}")
            send("isready")
            read_until(lambda line: line == "readyok")
            send("go depth 12")
            read_until(lambda line: line.startswith("bestmove "))
            if index % 50 == 0:
                print(f"position {index}", flush=True)
        send("quit")
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    open(out_path, "w", encoding="utf-8").write("\n".join(raw) + "\n")
    option_lines = [f"setoption name {name} value {value}" for name, value in options]
    meta = [
        f"exe: {exe}",
        f"sha256: {sha}",
        f"id name: {id_name}",
        "options:",
        *option_lines,
        f"fens: {fens_path}",
        f"positions: {len(fens)}",
        "search: go depth 12",
        "before each position: the option lines above, then ucinewgame, isready, position fen, isready",
    ]
    open(meta_path, "w", encoding="utf-8").write("\n".join(meta) + "\n")
    print(f"wrote {out_path} positions {len(fens)}")


if __name__ == "__main__":
    main()
