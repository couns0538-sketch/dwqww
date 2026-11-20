#!/usr/bin/env python3
"""One O-run: S14, Threads 1, Hash 16, go depth 12 on each FEN.

  python3 orun.py <exe> <prefix> <fens> [switch value]

A fresh process. After every setoption and every position: isready, read to
readyok. Stops on unknown option, invalid value, invalid FEN, illegal move.
Writes <prefix>.transcript (raw), <prefix>.rows (index and nodes of the last
info line before bestmove) and <prefix>.meta.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.q = queue.Queue()
        self.raw = []

        def reader():
            assert self.proc.stdout is not None
            for line in self.proc.stdout:
                self.q.put(line.rstrip("\n"))
            self.q.put(None)

        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def send(self, cmd):
        assert self.proc.stdin is not None
        self.raw.append(">> " + cmd)
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        deadline = time.time() + timeout
        got = []
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                sys.exit("STOP: timeout waiting for engine")
            try:
                line = self.q.get(timeout=remaining)
            except queue.Empty:
                sys.exit("STOP: timeout waiting for engine")
            if line is None:
                sys.exit("STOP: engine closed stdout")
            self.raw.append(line)
            got.append(line)
            for phrase in STOP:
                if phrase in line:
                    sys.exit(f"STOP: saw {phrase!r} in: {line}")
            if pred(line):
                return got

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def nodes_of(lines):
    last = None
    for line in lines:
        if line.startswith("info ") and " nodes " in line:
            last = int(line.split(" nodes ", 1)[1].split()[0])
    if last is None:
        sys.exit("STOP: no info nodes line before bestmove")
    return last


def main():
    if len(sys.argv) not in (4, 6):
        sys.exit("usage: orun.py <exe> <prefix> <fens> [switch value]")
    exe = str(Path(sys.argv[1]).resolve())
    prefix = Path(sys.argv[2])
    fens = [ln.strip() for ln in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")
    switch = None
    if len(sys.argv) == 6:
        switch = (sys.argv[4], sys.argv[5])
        if switch[1] not in ("true", "false"):
            sys.exit("STOP: switch value must be true or false")
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    eng = Engine(exe)
    id_name = "?"
    rows = []
    options = [
        "setoption name Threads value 1",
        "setoption name Hash value 16",
        *S14,
    ]
    if switch is not None:
        options.append(f"setoption name {switch[0]} value {switch[1]}")
    try:
        eng.send("uci")
        hello = eng.read_until(lambda ln: ln == "uciok", 60)
        id_name = next((ln[8:] for ln in hello if ln.startswith("id name ")), "?")
        eng.send("isready")
        eng.read_until(lambda ln: ln == "readyok", 60)
        for opt in options:
            eng.send(opt)
            eng.send("isready")
            eng.read_until(lambda ln: ln == "readyok", 60)
        rows = []
        for i, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda ln: ln == "readyok", 60)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda ln: ln == "readyok", 60)
            eng.send("go depth 12")
            info = eng.read_until(lambda ln: ln.startswith("bestmove "), 300)
            nodes = nodes_of(info)
            rows.append((i, nodes))
            print(f"{i} {nodes}", flush=True)
    finally:
        prefix.parent.mkdir(parents=True, exist_ok=True)
        prefix.with_suffix(".transcript").write_text("\n".join(eng.raw) + "\n", encoding="utf-8")
        prefix.with_suffix(".rows").write_text("".join(f"{i} {n}\n" for i, n in rows), encoding="utf-8")
        meta_opts = "\n".join(options) if options else "(none)"
        prefix.with_suffix(".meta").write_text(
            "\n".join(
                [
                    f"exe: {exe}",
                    f"sha256: {sha}",
                    f"id_name: {id_name}",
                    "options:",
                    meta_opts,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        eng.close()
    print(f"positions {len(rows)} sum {sum(n for _, n in rows)}", flush=True)


if __name__ == "__main__":
    main()
