#!/usr/bin/env python3
"""orun.py EXE OUTPREFIX FENS [SWITCH]

One engine process. S14, Threads 1, Hash 16, then optional SWITCH as name=true|false.
ucinewgame + isready before every position. go depth 12.
Stops on unknown option, invalid value, invalid FEN, illegal move.
Writes OUTPREFIX.txt (raw), OUTPREFIX.rows (pos, nodes) and OUTPREFIX.meta.
"""
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

S14 = (
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
)
STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Stop(Exception):
    def __init__(self, line):
        super().__init__(line)
        self.line = line


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.q = queue.Queue()
        self.lines = []

        def reader():
            for raw in self.proc.stdout:
                self.q.put(raw.decode("utf-8", "replace"))
            self.q.put(None)

        threading.Thread(target=reader, daemon=True).start()

    def send(self, text):
        self.proc.stdin.write((text + "\n").encode())
        self.proc.stdin.flush()

    def take(self, timeout):
        try:
            line = self.q.get(timeout=timeout)
        except queue.Empty:
            raise Stop("timeout waiting for engine")
        if line is None:
            raise Stop("engine closed stdout")
        self.lines.append(line)
        for mark in STOP_MARKS:
            if mark in line:
                raise Stop(line.rstrip("\n"))
        return line

    def read_until(self, pred, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                raise Stop("timeout waiting for engine")
            line = self.take(remain)
            if pred(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except (BrokenPipeError, Stop):
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nodes_of(info_line):
    parts = info_line.split()
    for i, part in enumerate(parts):
        if part == "nodes" and i + 1 < len(parts):
            return parts[i + 1]
    raise Stop(f"no nodes in info line: {info_line.rstrip()}")


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit("usage: orun.py EXE OUTPREFIX FENS [SWITCH=name=true|false]")
    exe, prefix, fens_path = sys.argv[1:4]
    switch = None
    if len(sys.argv) == 5:
        name, value = sys.argv[4].split("=", 1)
        if value not in ("true", "false"):
            sys.exit("switch value must be true or false")
        switch = (name, value)
    fens = [line.strip() for line in open(fens_path, encoding="utf-8") if line.strip()]
    sent = []
    rows = []
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line.startswith("uciok"), 30)
        for name, value in (("Threads", "1"), ("Hash", "16")) + S14 + ((switch,) if switch else ()):
            line = f"setoption name {name} value {value}"
            sent.append(line)
            eng.send(line)
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
        for index, fen in enumerate(fens, start=1):
            eng.send("ucinewgame")
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
            eng.send(f"position fen {fen}")
            eng.send("isready")
            eng.read_until(lambda got: got.startswith("readyok"), 30)
            eng.send("go depth 12")
            last_info = None
            deadline = time.monotonic() + 180
            while True:
                remain = deadline - time.monotonic()
                if remain <= 0:
                    raise Stop(f"timeout on position {index}")
                got = eng.take(remain)
                if got.startswith("info "):
                    last_info = got
                if got.startswith("bestmove "):
                    break
            if last_info is None:
                raise Stop(f"no info line before bestmove on position {index}")
            rows.append((index, nodes_of(last_info), last_info.rstrip("\n")))
            if index % 25 == 0:
                print(f"{prefix} {index}/{len(fens)}", file=sys.stderr, flush=True)
    finally:
        raw_path = prefix + ".txt"
        rows_path = prefix + ".rows"
        meta_path = prefix + ".meta"
        os.makedirs(os.path.dirname(os.path.abspath(prefix)) or ".", exist_ok=True)
        with open(raw_path, "w", encoding="utf-8") as f:
            f.writelines(eng.lines)
        with open(rows_path, "w", encoding="utf-8") as f:
            for index, nodes, info in rows:
                f.write(f"{index}\t{nodes}\t{info}\n")
        id_name = ""
        for line in eng.lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):].rstrip("\n")
                break
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"exe: {os.path.abspath(exe)}\n")
            f.write(f"sha256: {sha256_file(exe)}\n")
            f.write(f"id_name: {id_name}\n")
            f.write(f"fens: {os.path.abspath(fens_path)}\n")
            f.write(f"fens_sha256: {sha256_file(fens_path)}\n")
            f.write(f"fens_lines: {len(fens)}\n")
            f.write("options_sent:\n")
            for line in sent:
                f.write(line + "\n")
        eng.close()
    print(f"{prefix} positions {len(rows)}", flush=True)


if __name__ == "__main__":
    main()
