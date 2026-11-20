#!/usr/bin/env python3
"""Depth-12 node run over a FEN file. One engine process.

  python3 o_run.py <exe> <fens> <out> <meta> [SwitchName true|false]

Sends Threads 1 and Hash 16, then the S14 options in the brief's order,
then the switch when one is given. ucinewgame and isready before every
position. Stops on unknown option, invalid value, invalid FEN, illegal move.
"""
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [
    ("Threads", "1"),
    ("Hash", "16"),
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

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


class Engine:
    def __init__(self, path):
        self.path = path
        self.proc = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.lines = []
        self.queue = queue.Queue()

        def read():
            assert self.proc.stdout is not None
            for raw in self.proc.stdout:
                self.queue.put(raw.decode("utf-8", "replace").rstrip("\r\n"))
            self.queue.put(None)

        self.thread = threading.Thread(target=read, daemon=True)
        self.thread.start()

    def send(self, command):
        assert self.proc.stdin is not None
        self.proc.stdin.write((command + "\n").encode())
        self.proc.stdin.flush()

    def until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                sys.exit("STOP: timeout waiting for engine")
            try:
                line = self.queue.get(timeout=min(1.0, remaining))
            except queue.Empty:
                if self.proc.poll() is not None:
                    sys.exit(f"STOP: engine exited {self.proc.returncode}")
                continue
            if line is None:
                sys.exit(f"STOP: engine closed, exit {self.proc.poll()}")
            self.lines.append(line)
            for phrase in STOP:
                if phrase in line:
                    sys.exit(f"STOP: {line}")
            if predicate(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def main():
    if len(sys.argv) not in (5, 7):
        sys.exit("usage: o_run.py <exe> <fens> <out> <meta> [SwitchName true|false]")
    exe = os.path.abspath(sys.argv[1])
    fen_path, out_path, meta_path = sys.argv[2], sys.argv[3], sys.argv[4]
    switch = None
    if len(sys.argv) == 7:
        switch = (sys.argv[5], sys.argv[6])
        if switch[1] not in ("true", "false"):
            sys.exit("STOP: switch value must be true or false")
    fens = []
    with open(fen_path, encoding="utf-8") as handle:
        for line in handle:
            fen = line.strip()
            if fen:
                fens.append(fen)
    if len(fens) != 200:
        sys.exit(f"STOP: expected 200 fens, got {len(fens)}")

    options = list(S14)
    if switch is not None:
        options.append(switch)

    engine = Engine(exe)
    try:
        engine.send("uci")
        engine.until(lambda line: line == "uciok", 60)
        engine.send("isready")
        engine.until(lambda line: line == "readyok", 60)
        for name, value in options:
            engine.send(f"setoption name {name} value {value}")
            engine.send("isready")
            engine.until(lambda line: line == "readyok", 60)
        for fen in fens:
            engine.send("ucinewgame")
            engine.send("isready")
            engine.until(lambda line: line == "readyok", 60)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.until(lambda line: line == "readyok", 60)
            engine.send("go depth 12")
            engine.until(lambda line: line.startswith("bestmove "), 180)
    finally:
        text = "\n".join(engine.lines) + "\n"
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        name = ""
        for line in engine.lines:
            if line.startswith("id name "):
                name = line[len("id name "):]
                break
        with open(meta_path, "w", encoding="utf-8") as handle:
            handle.write(f"exe: {exe}\n")
            handle.write(f"sha256: {sha256_file(exe)}\n")
            handle.write(f"id name: {name}\n")
            handle.write("options:\n")
            for opt_name, value in options:
                handle.write(f"setoption name {opt_name} value {value}\n")
        engine.close()
    print(f"wrote {out_path} lines {len(engine.lines)}")


if __name__ == "__main__":
    main()
