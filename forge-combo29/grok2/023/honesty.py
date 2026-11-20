#!/usr/bin/env python3
"""Honesty check: one fresh engine process per command, no setoption before the command."""
import hashlib
import os
import select
import subprocess
import sys

FORBID = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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
        self.pending = b""

    def send(self, line):
        self.proc.stdin.write((line + "\n").encode())
        self.proc.stdin.flush()

    def read_until(self, predicate, timeout):
        import time
        deadline = time.monotonic() + timeout
        got = []
        while time.monotonic() < deadline:
            if self.pending:
                if b"\n" in self.pending:
                    raw, self.pending = self.pending.split(b"\n", 1)
                    line = raw.decode("utf-8", "replace").rstrip("\r")
                    got.append(line)
                    if predicate(line):
                        return got
                    continue
            wait = max(0.0, deadline - time.monotonic())
            r, _, _ = select.select([self.proc.stdout], [], [], min(1.0, wait))
            if not r:
                if self.proc.poll() is not None:
                    rest = self.proc.stdout.read() or b""
                    self.pending += rest
                    while b"\n" in self.pending:
                        raw, self.pending = self.pending.split(b"\n", 1)
                        line = raw.decode("utf-8", "replace").rstrip("\r")
                        got.append(line)
                        if predicate(line):
                            return got
                    break
                continue
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                break
            self.pending += chunk
        raise TimeoutError("timeout waiting for engine; got %d lines, last=%r" % (len(got), got[-1] if got else None))

    def close(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def check_forbid(lines):
    for line in lines:
        for bad in FORBID:
            if bad in line:
                raise SystemExit("STOP: %s" % line)


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <tag> <outdir>")
    exe, tag, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    digest = sha256_file(exe)
    jobs = [
        ("bench11", "bench 11", lambda line: line.startswith("info string bench depth 11 ")),
        ("bench13", "bench 13", lambda line: line.startswith("info string bench depth 13 ")),
        ("bench16", "bench 16", lambda line: line.startswith("info string bench depth 16 ")),
        ("perft5", "go perft 5", lambda line: line.startswith("nodes ")),
    ]
    for name, cmd, pred in jobs:
        eng = Engine(exe)
        try:
            eng.send(cmd)
            lines = eng.read_until(pred, 180.0)
            # id name after the measured command, so nothing precedes the measurement
            eng.send("uci")
            id_lines = eng.read_until(lambda line: line == "uciok", 10.0)
        finally:
            eng.close()
        all_lines = lines + id_lines
        check_forbid(all_lines)
        id_name = ""
        for line in id_lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        raw_path = os.path.join(outdir, "honesty_%s_%s.txt" % (tag, name))
        meta_path = raw_path + ".meta"
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_lines) + "\n")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write("exe=%s\n" % exe)
            f.write("sha256=%s\n" % digest)
            f.write("id name %s\n" % id_name)
            f.write("command=%s\n" % cmd)
            f.write("options:\n")
            f.write("(none before the measured command)\n")
        print("%s %s -> %s" % (tag, cmd, lines[-1] if lines else "NO LINE"))


if __name__ == "__main__":
    main()
