#!/usr/bin/env python3
"""Fresh-process honesty checks. No setoption. One command per process."""
import hashlib
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
COMMANDS = ["bench 11", "bench 13", "bench 16", "go perft 5"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.q = queue.Queue()
        self.lines = []

        def reader():
            while True:
                raw = self.proc.stdout.readline()
                if not raw:
                    self.q.put(None)
                    return
                self.q.put(raw.decode("utf-8", "replace"))

        self.thread = threading.Thread(target=reader, daemon=True)
        self.thread.start()

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, pred, timeout):
        end = time.time() + timeout
        got = []
        while time.time() < end:
            try:
                line = self.q.get(timeout=max(0.05, min(1.0, end - time.time())))
            except queue.Empty:
                continue
            if line is None:
                break
            self.lines.append(line)
            got.append(line)
            for bad in BAD:
                if bad in line:
                    raise SystemExit(f"STOP: {line.rstrip()}")
            if pred(line):
                return got
        raise SystemExit(f"STOP: timeout waiting after {self.lines[-1].rstrip() if self.lines else 'no output'}")

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def id_name(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):].rstrip("\n")
    return ""


def run_one(exe, command, stem):
    eng = Engine(exe)
    try:
        eng.send("uci")
        eng.read_until(lambda line: line.startswith("uciok"), 30)
        eng.send(command)
        if command.startswith("bench"):
            eng.read_until(lambda line: line.startswith("info string bench "), 180)
        else:
            eng.read_until(lambda line: line.startswith("nodes "), 180)
    finally:
        text = "".join(eng.lines)
        (OUT / f"{stem}.txt").write_text(text, encoding="utf-8")
        meta = (
            f"exe: {exe}\n"
            f"sha256: {sha256_file(exe)}\n"
            f"id_name: {id_name(eng.lines)}\n"
            f"command: {command}\n"
            "options:\n"
        )
        (OUT / f"{stem}.meta").write_text(meta, encoding="utf-8")
        eng.close()
    print(f"wrote {stem}", flush=True)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: honesty.py <exe> <tag>")
    exe = str(Path(sys.argv[1]).resolve())
    tag = sys.argv[2]
    for command in COMMANDS:
        slug = command.replace(" ", "")
        run_one(exe, command, f"honesty_{tag}_{slug}")


if __name__ == "__main__":
    main()
