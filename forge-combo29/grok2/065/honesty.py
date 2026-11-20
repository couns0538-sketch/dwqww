#!/usr/bin/env python3
"""honesty.py EXE TAG OUTDIR

Fresh process for each line. Nothing is sent before the measured command.
TAG is B or P. Writes TAG raw transcripts and .meta files into OUTDIR.
"""
import hashlib
import os
import queue
import subprocess
import sys
import threading
import time

COMMANDS = ("bench 11", "bench 13", "bench 16", "go perft 5")


class Engine:
    def __init__(self, exe):
        self.exe = exe
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

    def read_until(self, pred, timeout):
        deadline = time.monotonic() + timeout
        while True:
            remain = deadline - time.monotonic()
            if remain <= 0:
                return False
            try:
                line = self.q.get(timeout=remain)
            except queue.Empty:
                return False
            if line is None:
                return False
            self.lines.append(line)
            if pred(line):
                return True

    def close(self):
        try:
            self.send("quit")
        except BrokenPipeError:
            pass
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def id_name_from(lines):
    for line in lines:
        if line.startswith("id name "):
            return line[len("id name "):].rstrip("\n")
    return ""


def slug(command):
    return command.replace(" ", "")


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py EXE TAG OUTDIR")
    exe, tag, outdir = sys.argv[1:]
    os.makedirs(outdir, exist_ok=True)
    exe_hash = sha256_file(exe)
    for command in COMMANDS:
        eng = Engine(exe)
        eng.send(command)
        if command.startswith("bench"):
            ok = eng.read_until(lambda line: line.startswith("info string bench "), 180)
        else:
            ok = eng.read_until(lambda line: line.startswith("nodes "), 180)
        eng.send("uci")
        eng.read_until(lambda line: line.startswith("uciok"), 30)
        eng.close()
        name = f"honesty_{tag}_{slug(command)}"
        raw_path = os.path.join(outdir, name + ".txt")
        meta_path = os.path.join(outdir, name + ".meta")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.writelines(eng.lines)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"exe: {exe}\n")
            f.write(f"sha256: {exe_hash}\n")
            f.write(f"id_name: {id_name_from(eng.lines)}\n")
            f.write("options_sent:\n")
            f.write("(none)\n")
            f.write(f"command: {command}\n")
            f.write(f"saw_result: {ok}\n")
        print(f"{name} saw_result={ok} lines={len(eng.lines)}", flush=True)
        if not ok:
            sys.exit(f"STOP: no result for {command}")


if __name__ == "__main__":
    main()
