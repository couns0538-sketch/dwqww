#!/usr/bin/env python3
"""Depth-12 node run. S14, then Threads 1, then Hash 16, then an optional switch.

Usage: orun.py EXE FENS OUT_RAW OUT_META [SWITCH true|false]
A fresh process. isready after every setoption and every position. Stops on a refusal.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_until(proc, lines, ok):
    while True:
        line = proc.stdout.readline()
        if line == "":
            sys.exit("STOP: engine closed stdout")
        line = line.rstrip("\r\n")
        lines.append(line)
        for token in BAD:
            if token in line:
                sys.exit(f"STOP: {line}")
        if ok(line):
            return line


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: orun.py EXE FENS OUT_RAW OUT_META [SWITCH true|false]")
    exe = str(Path(sys.argv[1]).resolve())
    fens_path = Path(sys.argv[2])
    out_raw = Path(sys.argv[3])
    out_meta = Path(sys.argv[4])
    options = list(S14)
    if len(sys.argv) == 7:
        switch, value = sys.argv[5], sys.argv[6]
        if value not in ("true", "false"):
            sys.exit("STOP: switch value must be true or false")
        options.append((switch, value))
    fens = [line.strip() for line in fens_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    digest = sha256_file(exe)
    fens_sha = sha256_file(fens_path)
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
    sent = []
    try:
        proc.stdin.write("uci\n")
        proc.stdin.flush()

        def capture(line):
            nonlocal id_name
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            return line == "uciok"

        read_until(proc, lines, capture)
        proc.stdin.write("isready\n")
        proc.stdin.flush()
        read_until(proc, lines, lambda line: line == "readyok")
        for name, value in options:
            cmd = f"setoption name {name} value {value}"
            sent.append(cmd)
            proc.stdin.write(cmd + "\n")
            proc.stdin.flush()
            proc.stdin.write("isready\n")
            proc.stdin.flush()
            read_until(proc, lines, lambda line: line == "readyok")
        for fen in fens:
            proc.stdin.write("ucinewgame\n")
            proc.stdin.flush()
            proc.stdin.write("isready\n")
            proc.stdin.flush()
            read_until(proc, lines, lambda line: line == "readyok")
            proc.stdin.write(f"position fen {fen}\n")
            proc.stdin.flush()
            proc.stdin.write("isready\n")
            proc.stdin.flush()
            read_until(proc, lines, lambda line: line == "readyok")
            proc.stdin.write("go depth 12\n")
            proc.stdin.flush()
            read_until(proc, lines, lambda line: line.startswith("bestmove "))
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=60)
    finally:
        if proc.poll() is None:
            proc.kill()
    out_raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = [
        f"exe: {exe}",
        f"sha256: {digest}",
        f"id name: {id_name}",
        f"fens: {fens_path.resolve()}",
        f"fens_sha256: {fens_sha}",
        "options:",
        *sent,
    ]
    out_meta.write_text("\n".join(meta) + "\n", encoding="utf-8")
    print(f"wrote {out_raw} positions {len(fens)}")


if __name__ == "__main__":
    main()
