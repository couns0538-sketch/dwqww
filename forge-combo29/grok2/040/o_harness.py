#!/usr/bin/env python3
"""O-run harness. One engine process. S14, then Threads and Hash, then an optional switch.
After every setoption and every position: isready, and every line is read up to readyok.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import os
import select
import subprocess
import sys
import time

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
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
    "setoption name Threads value 1",
    "setoption name Hash value 16",
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.pending = b""
        self.lines = []

    def send(self, line):
        self.lines.append(">> " + line)
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_line(self, timeout):
        end = time.monotonic() + timeout
        while b"\n" not in self.pending:
            remaining = end - time.monotonic()
            if remaining <= 0:
                sys.exit("STOP: timeout waiting for engine")
            ready, _, _ = select.select([self.proc.stdout], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if chunk == b"":
                sys.exit("STOP: engine closed stdout")
            self.pending += chunk
        raw, self.pending = self.pending.split(b"\n", 1)
        line = raw.decode("utf-8", "replace").rstrip("\r")
        self.lines.append(line)
        for mark in STOP_MARKS:
            if mark in line:
                sys.exit("STOP: " + line)
        return line

    def read_until(self, predicate, timeout):
        end = time.monotonic() + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                sys.exit("STOP: timeout waiting for engine")
            line = self.read_line(remaining)
            if predicate(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: o_harness.py <exe> <fens> <out> <meta> [<switch> <true|false>]")
    exe, fens_path, out_path, meta_path = sys.argv[1:5]
    switch = sys.argv[5] if len(sys.argv) == 7 else ""
    switch_value = sys.argv[6] if len(sys.argv) == 7 else ""
    if switch_value not in ("", "true", "false"):
        sys.exit("STOP: switch value must be true or false")
    options = list(S14)
    if switch:
        options.append(f"setoption name {switch} value {switch_value}")
    with open(fens_path, encoding="utf-8") as handle:
        fens = [line.strip() for line in handle if line.strip()]
    engine = Engine(exe)
    id_name = ""
    try:
        engine.send("uci")
        engine.read_until(lambda line: line == "uciok", 30)
        id_name = ""
        for line in engine.lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        for option in options:
            engine.send(option)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("position fen " + fen)
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove "), 180)
    finally:
        engine.close()
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(engine.lines) + "\n")
        with open(meta_path, "w", encoding="utf-8") as handle:
            handle.write(f"exe: {exe}\n")
            handle.write(f"sha256: {sha256_file(exe)}\n")
            handle.write(f"id name: {id_name}\n")
            handle.write("options:\n")
            for option in options:
                handle.write(option + "\n")
    print(f"wrote {out_path} positions {len(fens)}")


if __name__ == "__main__":
    main()
