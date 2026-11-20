#!/usr/bin/env python3
"""UCI harness for the honesty checks and the 200-position O runs.

A fresh engine process is used for every honesty command. No setoption is sent
before an honesty command. O runs send S14, then Threads 1, then Hash 16, then
the switch when one is named. After every setoption and every position the
harness sends isready and reads every line up to readyok. It stops on
"unknown option", "invalid value", "invalid FEN" or "illegal move".

Usage:
  harness.py honesty <exe> <outdir> <tag>
  harness.py orun <exe> <outdir> <name> <fens> [switch true|false]
"""

import hashlib
import os
import subprocess
import sys
import threading
import time

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


class ProtocolError(Exception):
    pass


class Engine:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.proc = subprocess.Popen(
            [self.path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""
        self.lines = []
        self.cursor = 0
        self.lock = threading.Lock()
        self.closed = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        while True:
            chunk = self.proc.stdout.read(4096)
            if not chunk:
                with self.lock:
                    self.closed = True
                return
            with self.lock:
                self.buf += chunk
                while b"\n" in self.buf:
                    raw, self.buf = self.buf.split(b"\n", 1)
                    self.lines.append(raw.decode("utf-8", "replace").rstrip("\r"))

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def wait_pred(self, pred, timeout):
        # Only lines received after the previous match count. A later wait must
        # not treat an earlier bestmove or readyok as the one just asked for.
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                lines = self.lines
                dead = self.closed
            while self.cursor < len(lines):
                text = lines[self.cursor]
                self.cursor += 1
                for marker in STOP_MARKERS:
                    if marker in text:
                        raise ProtocolError(text)
                if pred(text):
                    return
            if dead:
                raise ProtocolError("engine exited before the expected line")
            time.sleep(0.01)
        raise ProtocolError("timeout waiting for the engine")

    def snapshot(self):
        with self.lock:
            return list(self.lines)

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def id_name_from(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def write_output(out_path, lines, exe, id_name, options):
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        if lines:
            handle.write("\n")
    meta_path = out_path + ".meta"
    with open(meta_path, "w", encoding="utf-8") as handle:
        handle.write("exe " + exe + "\n")
        handle.write("sha256 " + sha256_file(exe) + "\n")
        handle.write("id name " + id_name + "\n")
        for option in options:
            handle.write(option + "\n")


def handshake(engine):
    engine.send("uci")
    engine.wait_pred(lambda line: line == "uciok", 60)
    return id_name_from(engine.snapshot())


def ready(engine):
    engine.send("isready")
    engine.wait_pred(lambda line: line == "readyok", 60)


def setoption(engine, name, value, sent):
    line = f"setoption name {name} value {value}"
    engine.send(line)
    sent.append(line)
    ready(engine)


def honesty(exe, outdir, tag):
    commands = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench depth 11 nodes "), 180),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench depth 13 nodes "), 180),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench depth 16 nodes "), 300),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes "), 180),
    ]
    os.makedirs(outdir, exist_ok=True)
    for name, command, pred, timeout in commands:
        engine = Engine(exe)
        try:
            id_name = handshake(engine)
            engine.send(command)
            engine.wait_pred(pred, timeout)
            engine.close()
            time.sleep(0.05)
            lines = engine.snapshot()
            out_path = os.path.join(outdir, f"honesty_{tag}_{name}.txt")
            write_output(out_path, lines, engine.path, id_name, [])
            print(f"wrote {out_path}")
        finally:
            if engine.proc.poll() is None:
                engine.close()


def orun(exe, outdir, name, fens_path, switch, switch_value):
    with open(fens_path, encoding="utf-8") as handle:
        fens = [line.strip() for line in handle if line.strip()]
    engine = Engine(exe)
    sent = []
    try:
        id_name = handshake(engine)
        for opt_name, opt_value in S14:
            setoption(engine, opt_name, opt_value, sent)
        setoption(engine, "Threads", "1", sent)
        setoption(engine, "Hash", "16", sent)
        if switch:
            setoption(engine, switch, switch_value, sent)
        for index, fen in enumerate(fens, start=1):
            engine.send("ucinewgame")
            ready(engine)
            engine.send("position fen " + fen)
            ready(engine)
            engine.send("go depth 12")
            engine.wait_pred(lambda line: line.startswith("bestmove "), 180)
            if index % 50 == 0:
                print(f"{name} position {index}", flush=True)
        engine.close()
        time.sleep(0.05)
        lines = engine.snapshot()
        out_path = os.path.join(outdir, f"{name}.txt")
        write_output(out_path, lines, engine.path, id_name, sent)
        print(f"wrote {out_path} positions {len(fens)}")
    finally:
        if engine.proc.poll() is None:
            engine.close()


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    mode = sys.argv[1]
    if mode == "honesty":
        honesty(sys.argv[2], sys.argv[3], sys.argv[4])
    elif mode == "orun":
        switch = None
        switch_value = None
        if len(sys.argv) >= 8:
            switch = sys.argv[6]
            switch_value = sys.argv[7]
        orun(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], switch, switch_value)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    try:
        main()
    except ProtocolError as exc:
        print(f"STOP {exc}", file=sys.stderr)
        sys.exit(2)
