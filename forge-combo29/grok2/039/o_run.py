#!/usr/bin/env python3
"""O depth-12 run. S14, Threads 1, Hash 16, then optional switch.

Usage: python3 o_run.py <exe> <fens> <out.txt> <meta.txt> [SwitchName true|false]
A fresh process. ucinewgame + isready before every position. go depth 12.
Raw stdout is saved unchanged. Stops on unknown option, invalid value,
invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
from pathlib import Path

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit(__doc__)
    exe = str(Path(sys.argv[1]).resolve())
    fens = Path(sys.argv[2]).read_text(encoding="utf-8").splitlines()
    fens = [line.strip() for line in fens if line.strip()]
    out_path = Path(sys.argv[3])
    meta_path = Path(sys.argv[4])
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if len(sys.argv) == 7:
        options.append(f"setoption name {sys.argv[5]} value {sys.argv[6]}")

    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines = []
    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def read_line(timeout, what):
        try:
            item = q.get(timeout=timeout)
        except queue.Empty:
            proc.kill()
            out_path.write_text("".join(lines), encoding="utf-8")
            raise SystemExit(f"STOP: timeout during {what}")
        if item is None:
            out_path.write_text("".join(lines), encoding="utf-8")
            raise SystemExit(f"STOP: engine closed stdout during {what}")
        line = item if item.endswith("\n") else item + "\n"
        lines.append(line)
        bare = line.rstrip("\n")
        for marker in STOP_MARKERS:
            if marker in bare:
                out_path.write_text("".join(lines), encoding="utf-8")
                proc.kill()
                raise SystemExit(f"STOP: {bare}")
        return bare

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def ready(what):
        send("isready")
        while read_line(60, what) != "readyok":
            pass

    id_name = ""
    send("uci")
    while True:
        line = read_line(60, "uci")
        if line.startswith("id name "):
            id_name = line[len("id name "):]
        if line == "uciok":
            break
    ready("uci isready")
    for option in options:
        send(option)
        ready(option)
    for index, fen in enumerate(fens, start=1):
        send("ucinewgame")
        ready(f"ucinewgame {index}")
        send(f"position fen {fen}")
        ready(f"position {index}")
        send("go depth 12")
        while read_line(180, f"go {index}") != "bestmove" and not lines[-1].startswith("bestmove "):
            pass
        if index % 25 == 0 or index == len(fens):
            print(f"{out_path.name} position {index}/{len(fens)}", flush=True)
    send("quit")
    proc.wait(timeout=30)
    out_path.write_text("".join(lines), encoding="utf-8")
    meta = [
        f"exe={exe}",
        f"sha256={sha256_file(exe)}",
        f"id_name={id_name}",
        "options:",
        *options,
        "",
    ]
    meta_path.write_text("\n".join(meta), encoding="utf-8")
    print(f"wrote {out_path} positions {len(fens)}", flush=True)


if __name__ == "__main__":
    main()
