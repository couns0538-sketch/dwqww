#!/usr/bin/env python3
"""Honesty checks: one fresh engine process per command, no setoption.

Usage: python3 honesty.py <exe> <outdir> <tag>
Writes <tag>_bench11, <tag>_bench13, <tag>_bench16, <tag>_perft5 (.txt and .meta).
"""
import hashlib
import queue
import subprocess
import sys
import threading
from pathlib import Path

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = str(Path(exe).resolve())
        self.proc = subprocess.Popen(
            [self.exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.raw = []
        self.id_name = ""
        self.lines = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send(self, line):
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        while True:
            try:
                line = self.lines.get(timeout=timeout)
            except queue.Empty:
                raise SystemExit(f"STOP: timeout after {timeout}s")
            if line is None:
                raise SystemExit(f"STOP: engine exited {self.proc.poll()}")
            self.raw.append(line)
            for mark in STOP_MARKS:
                if mark in line:
                    raise SystemExit(f"STOP: {line.rstrip()}")
            if line.startswith("id name "):
                self.id_name = line[len("id name ") :].rstrip("\r\n")
            if pred(line):
                return line

    def close(self):
        try:
            self.send("quit")
        except OSError:
            pass
        try:
            self.proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def handshake(engine):
    engine.send("uci")
    engine.read_until(lambda line: line.startswith("uciok"), 30)


def write_pair(outdir, tag, engine, command):
    raw_path = outdir / f"{tag}.txt"
    meta_path = outdir / f"{tag}.meta"
    raw_path.write_text("".join(engine.raw), encoding="utf-8")
    meta = [
        f"exe={engine.exe}",
        f"sha256={sha256_file(engine.exe)}",
        f"id_name={engine.id_name}",
        f"command={command}",
        "options=",
    ]
    meta_path.write_text("\n".join(meta) + "\n", encoding="utf-8")


def run_one(exe, outdir, tag, command, pred, timeout):
    engine = Engine(exe)
    try:
        handshake(engine)
        engine.send(command)
        engine.read_until(pred, timeout)
    finally:
        engine.close()
        write_pair(outdir, tag, engine, command)
    print(f"{tag} ok id={engine.id_name}")


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: honesty.py <exe> <outdir> <tag>")
    exe, outdir, tag = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    outdir.mkdir(parents=True, exist_ok=True)
    run_one(exe, outdir, f"{tag}_bench11", "bench 11", lambda line: "bench depth 11 nodes " in line, 120)
    run_one(exe, outdir, f"{tag}_bench13", "bench 13", lambda line: "bench depth 13 nodes " in line, 180)
    run_one(exe, outdir, f"{tag}_bench16", "bench 16", lambda line: "bench depth 16 nodes " in line, 300)
    run_one(
        exe,
        outdir,
        f"{tag}_perft5",
        "go perft 5",
        lambda line: line.startswith("nodes "),
        120,
    )


if __name__ == "__main__":
    main()
