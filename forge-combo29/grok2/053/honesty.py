#!/usr/bin/env python3
"""Honesty check: one fresh engine process per command, no setoption.

Writes raw stdout and a .meta beside it.
Usage: honesty.py <exe> <label> <outdir>
"""
import hashlib
import os
import select
import subprocess
import sys

COMMANDS = [
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
]
STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


class Engine:
    def __init__(self, exe):
        self.proc = subprocess.Popen(
            [exe],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )
        self.buf = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def readline(self, timeout):
        while b"\n" not in self.buf:
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                raise TimeoutError(f"no output for {timeout}s")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError("engine closed stdout")
            self.buf += chunk
        raw, self.buf = self.buf.split(b"\n", 1)
        return raw.decode("utf-8", "replace").rstrip("\r")

    def close(self):
        try:
            if self.proc.poll() is None:
                self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
            self.proc.wait(timeout=5)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def id_name(exe):
    eng = Engine(exe)
    try:
        eng.send("uci")
        name = ""
        while True:
            line = eng.readline(30)
            if line.startswith("id name "):
                name = line[len("id name "):]
            if line == "uciok":
                return name
    finally:
        eng.close()


def nodes_of(tag, text):
    if tag.startswith("bench"):
        # info string bench depth N nodes X time ...
        for line in text.splitlines():
            if " nodes " in line and line.startswith("info string bench"):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
        raise ValueError("no bench nodes line")
    last = None
    for line in text.splitlines():
        if line.startswith("nodes "):
            last = int(line.split()[1])
    if last is None:
        raise ValueError("no perft nodes line")
    return last


def run_one(exe, command, out_path, meta_path, exe_sha, name):
    eng = Engine(exe)
    lines = []
    try:
        eng.send(command)
        deadline_reads = 0
        # Bench and perft are synchronous and print their summary at the end.
        while True:
            line = eng.readline(180)
            lines.append(line)
            for bad in STOP:
                if bad in line:
                    raise SystemExit(f"STOP: {line}")
            if command.startswith("bench") and line.startswith("info string bench"):
                break
            if command.startswith("go perft") and line.startswith("nodes "):
                break
            deadline_reads += 1
            if deadline_reads > 100000:
                raise SystemExit("STOP: too many lines")
    finally:
        text = "\n".join(lines) + ("\n" if lines else "")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"exe: {exe}\n")
            f.write(f"sha256: {exe_sha}\n")
            f.write(f"id_name: {name}\n")
            f.write("options:\n")
            f.write(f"command: {command}\n")
        eng.close()
    return text


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <label> <outdir>")
    exe, label, outdir = sys.argv[1:]
    os.makedirs(outdir, exist_ok=True)
    exe_sha = sha256_file(exe)
    name = id_name(exe)
    print(f"exe {exe}")
    print(f"sha256 {exe_sha}")
    print(f"id_name {name}")
    failed = False
    for tag, command, expected in COMMANDS:
        out_path = os.path.join(outdir, f"honesty_{label}_{tag}.txt")
        meta_path = os.path.join(outdir, f"honesty_{label}_{tag}.meta")
        text = run_one(exe, command, out_path, meta_path, exe_sha, name)
        got = nodes_of(tag, text)
        status = "OK" if got == expected else "MISS"
        if status != "OK":
            failed = True
        print(f"{label} {command} nodes {got} expected {expected} {status}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
