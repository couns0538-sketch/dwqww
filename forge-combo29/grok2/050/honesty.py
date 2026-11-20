#!/usr/bin/env python3
"""honesty.py EXE LABEL OUTDIR

Fresh engine process for each line. No setoption. Raw stdout saved beside a .meta file.
"""
import hashlib
import os
import select
import subprocess
import sys
import time

STOP_MARKS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
COMMANDS = (
    ("bench11", "bench 11", "info string bench depth 11 nodes 312866"),
    ("bench13", "bench 13", "info string bench depth 13 nodes 862329"),
    ("bench16", "bench 16", "info string bench depth 16 nodes 3024920"),
    ("perft5", "go perft 5", "nodes 4865609"),
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def bad_line(line):
    return any(mark in line for mark in STOP_MARKS)


def read_until(proc, lines, pred, timeout):
    buf = b""
    end = time.monotonic() + timeout
    while True:
        if pred():
            return
        remaining = end - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("timeout after %d lines" % len(lines))
        ready, _, _ = select.select([proc.stdout], [], [], remaining)
        if not ready:
            raise TimeoutError("timeout after %d lines" % len(lines))
        chunk = os.read(proc.stdout.fileno(), 65536)
        if not chunk:
            if pred():
                return
            raise EOFError("engine closed stdout after %d lines" % len(lines))
        buf += chunk
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            line = raw.decode("utf-8", "replace").rstrip("\r")
            lines.append(line)
            if bad_line(line):
                raise RuntimeError("STOP: " + line)
            if pred():
                return


def run_one(exe, label, outdir, tag, command, expect):
    lines = []
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    id_name = ""
    try:
        proc.stdin.write(b"uci\n")
        proc.stdin.flush()

        def have_uciok():
            return any(line == "uciok" for line in lines)

        read_until(proc, lines, have_uciok, 60)
        for line in lines:
            if line.startswith("id name "):
                id_name = line[len("id name "):]
        proc.stdin.write((command + "\n").encode())
        proc.stdin.flush()
        before = len(lines)

        def have_expect():
            return any(expect in line for line in lines[before:])

        read_until(proc, lines, have_expect, 180)
        proc.stdin.write(b"quit\n")
        proc.stdin.flush()
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)
        err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""

    stem = os.path.join(outdir, "honesty_%s_%s" % (label, tag))
    with open(stem + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    if err:
        with open(stem + ".err", "w", encoding="utf-8") as f:
            f.write(err)
    with open(stem + ".meta", "w", encoding="utf-8") as f:
        f.write("exe: %s\n" % exe)
        f.write("sha256: %s\n" % sha256_file(exe))
        f.write("id name: %s\n" % id_name)
        f.write("command: %s\n" % command)
        f.write("options:\n")
        f.write("(none)\n")
    hit = [line for line in lines if expect in line]
    print("%s %s %s" % (label, tag, "PASS" if hit else "FAIL"))
    if not hit:
        raise SystemExit("missing expected output for %s" % tag)
    return id_name


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: honesty.py EXE LABEL OUTDIR")
    exe, label, outdir = sys.argv[1:]
    os.makedirs(outdir, exist_ok=True)
    for tag, command, expect in COMMANDS:
        run_one(exe, label, outdir, tag, command, expect)
    print("honesty %s ok" % label)


if __name__ == "__main__":
    main()
