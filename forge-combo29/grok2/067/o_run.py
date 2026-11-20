#!/usr/bin/env python3
"""o_run.py EXE RAW META MODE [limit]
MODE is B, off, or on.
Sends S14, Threads 1, Hash 16. off/on also send IdeaK4 false/true.
Stops on unknown option, invalid value, invalid FEN, illegal move.
One row is not written here: o_rows.py reads RAW.
"""
import hashlib
import subprocess
import sys

FENS = "/home/ubuntu/first200.fens"
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
BAD = ("unknown option", "invalid value", "invalid fen", "illegal move")


def main():
    exe, raw_path, meta_path, mode = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    if mode not in ("B", "off", "on"):
        sys.exit(f"STOP: mode {mode}")
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if mode == "off":
        options.append("setoption name IdeaK4 value false")
    elif mode == "on":
        options.append("setoption name IdeaK4 value true")
    sha = hashlib.sha256(open(exe, "rb").read()).hexdigest()
    fens = [ln.strip() for ln in open(FENS, encoding="utf-8") if ln.strip()]
    if limit:
        fens = fens[:limit]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    id_name = ""
    with open(raw_path, "w", encoding="utf-8") as raw:
        def send(line):
            raw.write(">> " + line + "\n")
            raw.flush()
            proc.stdin.write(line + "\n")
            proc.stdin.flush()

        def read_until(done):
            nonlocal id_name
            while True:
                line = proc.stdout.readline()
                if line == "":
                    sys.exit("STOP: engine closed stdout")
                line = line.rstrip("\r\n")
                raw.write(line + "\n")
                raw.flush()
                low = line.lower()
                if any(b in low for b in BAD):
                    sys.exit("STOP: " + line)
                if line.startswith("id name "):
                    id_name = line[len("id name "):]
                if done(line):
                    return

        send("uci")
        read_until(lambda line: line == "uciok")
        for opt in options:
            send(opt)
            send("isready")
            read_until(lambda line: line == "readyok")
        for fen in fens:
            send("ucinewgame")
            send("isready")
            read_until(lambda line: line == "readyok")
            send("position fen " + fen)
            send("isready")
            read_until(lambda line: line == "readyok")
            send("go depth 12")
            read_until(lambda line: line.startswith("bestmove "))
        send("quit")
        proc.stdin.close()
        rest = proc.stdout.read()
        if rest:
            raw.write(rest)
        proc.wait(timeout=30)
    with open(meta_path, "w", encoding="utf-8") as meta:
        meta.write(f"exe {exe}\n")
        meta.write(f"sha256 {sha}\n")
        meta.write(f"id name {id_name}\n")
        meta.write(f"mode {mode}\n")
        meta.write(f"positions {len(fens)}\n")
        for opt in options:
            meta.write(opt + "\n")
    print(f"done {mode} positions {len(fens)} -> {raw_path}")


if __name__ == "__main__":
    main()
