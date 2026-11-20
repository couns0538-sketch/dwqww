#!/usr/bin/env python3
"""UCI harness for grok2 seat 029. Fresh process per honesty line; one process per O run.
Stops on unknown option, invalid value, invalid FEN, or illegal move.
"""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

STOP_BITS = ("unknown option", "invalid value", "invalid FEN", "illegal move")

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


class Stop(Exception):
    pass


class Engine:
    def __init__(self, exe, raw_path):
        self.exe = str(Path(exe).resolve())
        self.raw = open(raw_path, "w", encoding="utf-8")
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.q = queue.Queue()
        self.err = []

        def read_out():
            for raw in self.proc.stdout:
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                self.raw.write(line + "\n")
                self.raw.flush()
                self.q.put(line)
            self.q.put(None)

        def read_err():
            for raw in self.proc.stderr:
                self.err.append(raw.decode("utf-8", "replace").rstrip("\r\n"))

        threading.Thread(target=read_out, daemon=True).start()
        threading.Thread(target=read_err, daemon=True).start()
        self.id_name = ""
        self.options = []

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        end = time.time() + timeout
        got = []
        while time.time() < end:
            try:
                line = self.q.get(timeout=min(1.0, max(0.05, end - time.time())))
            except queue.Empty:
                if self.proc.poll() is not None and self.q.empty():
                    raise Stop(f"engine exited rc={self.proc.returncode} before the expected line")
                continue
            if line is None:
                raise Stop(f"engine closed stdout rc={self.proc.poll()}")
            got.append(line)
            if line.startswith("id name ") and not self.id_name:
                self.id_name = line[len("id name "):]
            for bit in STOP_BITS:
                if bit in line:
                    raise Stop(f"STOP {bit}: {line}")
            if pred(line):
                return got
        raise Stop(f"timeout after {timeout}s waiting; last={got[-3:]}")

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.raw.close()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_meta(path, engine, note):
    lines = [
        f"exe={engine.exe}",
        f"sha256={sha256_file(engine.exe)}",
        f"id_name={engine.id_name}",
        f"note={note}",
        "options:",
    ]
    lines.extend(engine.options if engine.options else ["(none)"])
    if engine.err:
        lines.append("stderr:")
        lines.extend(engine.err)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def handshake(engine):
    engine.send("uci")
    engine.read_until(lambda line: line == "uciok", 30)


def setoption(engine, name, value):
    line = f"setoption name {name} value {value}"
    engine.options.append(line)
    engine.send(line)
    engine.send("isready")
    engine.read_until(lambda s: s == "readyok", 30)


def honesty_one(exe, out_path, command):
    engine = Engine(exe, out_path)
    try:
        handshake(engine)
        engine.send(command)
        if command.startswith("bench"):
            engine.read_until(lambda line: line.startswith("info string bench "), 180)
        elif command.startswith("go perft"):
            engine.read_until(lambda line: line.startswith("nodes "), 180)
        else:
            raise Stop(f"unexpected command {command}")
    finally:
        engine.close()
    write_meta(out_path + ".meta", engine, command)


def orun(exe, out_path, fens_path, switch):
    fens = [ln.strip() for ln in Path(fens_path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if len(fens) != 200:
        raise Stop(f"expected 200 fens, got {len(fens)}")
    engine = Engine(exe, out_path)
    try:
        handshake(engine)
        setoption(engine, "Hash", "16")
        setoption(engine, "Threads", "1")
        for name, value in S14:
            setoption(engine, name, value)
        if switch is not None:
            name, value = switch
            setoption(engine, name, value)
        for index, fen in enumerate(fens, 1):
            engine.send("ucinewgame")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send(f"position fen {fen}")
            engine.send("isready")
            engine.read_until(lambda line: line == "readyok", 30)
            engine.send("go depth 12")
            engine.read_until(lambda line: line.startswith("bestmove "), 120)
            if index % 25 == 0:
                print(f"{out_path} position {index}", file=sys.stderr, flush=True)
    finally:
        engine.close()
    write_meta(out_path + ".meta", engine, f"orun fens={fens_path} switch={switch}")


def main():
    mode = sys.argv[1]
    if mode == "honesty":
        exe, out_prefix = sys.argv[2], sys.argv[3]
        for command, tag in (
            ("bench 11", "bench11"),
            ("bench 13", "bench13"),
            ("bench 16", "bench16"),
            ("go perft 5", "perft5"),
        ):
            honesty_one(exe, f"{out_prefix}_{tag}.txt", command)
            print(f"wrote {out_prefix}_{tag}.txt", flush=True)
    elif mode == "orun":
        exe, out_path, fens = sys.argv[2], sys.argv[3], sys.argv[4]
        switch = None
        if len(sys.argv) == 7:
            switch = (sys.argv[5], sys.argv[6])
        orun(exe, out_path, fens, switch)
        print(f"wrote {out_path}", flush=True)
    else:
        sys.exit("usage: harness.py honesty EXE PREFIX | harness.py orun EXE OUT FENS [SWITCH true|false]")


if __name__ == "__main__":
    try:
        main()
    except Stop as exc:
        print(f"HARNESS STOP: {exc}", file=sys.stderr)
        sys.exit(2)
