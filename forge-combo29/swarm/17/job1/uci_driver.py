#!/usr/bin/env python3
"""seat 17 harness: drive a UCI engine properly.

Sends one position + one go, reads output until `bestmove` (or timeout), only then
sends quit. Every line is written to the log. A missing readyok or bestmove is an error,
not silently ignored.
"""
import json
import os
import subprocess
import sys
import time


def run_one(exe, lines, timeout_s, log_path, env=None):
    """lines: list of commands (no trailing newline). Returns dict with output and result."""
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    out = []
    bestmove = None
    readyok = 0
    start = time.monotonic()
    timed_out = False
    try:
        for line in lines:
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            if line.startswith("go"):
                deadline = time.monotonic() + timeout_s
                while True:
                    if time.monotonic() > deadline:
                        timed_out = True
                        proc.kill()
                        break
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    out.append(reply.rstrip("\n"))
                    if reply.startswith("bestmove"):
                        bestmove = reply.strip()
                        break
            elif line == "isready":
                deadline = time.monotonic() + 30
                while True:
                    if time.monotonic() > deadline:
                        timed_out = True
                        break
                    reply = proc.stdout.readline()
                    if reply == "":
                        break
                    out.append(reply.rstrip("\n"))
                    if reply.strip() == "readyok":
                        readyok += 1
                        break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
    except BrokenPipeError:
        pass
    elapsed = time.monotonic() - start
    try:
        rc = proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait()
    with open(log_path, "w") as handle:
        handle.write("\n".join(out) + "\n")
    return {
        "bestmove": bestmove,
        "readyok": readyok,
        "rc": rc,
        "timed_out": timed_out,
        "elapsed_s": round(elapsed, 3),
        "lines": len(out),
    }
