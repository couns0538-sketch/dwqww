#!/usr/bin/env python3
"""Job 4 part A: drive the tracing engine with stdin held open and wait for bestmove.

Piping a whole command list into the engine closes stdin and the search is cut off
before it reports anything (measured: `bestmove` only, no `info depth`). This driver
writes one command at a time and blocks on `bestmove`, which is what makes the trace
mean anything.

Usage: a_drive.py <engine> <fen> [moves ...] [-- go <limit>] [--setopt name=value ...]
Prints stdout (info/bestmove) and stderr (TRACE lines) separately.
"""
import queue
import subprocess
import sys
import threading
import time


def run(engine, fen, moves, limit, setopts, env, timeout=300):
    commands = ["setoption name Threads value 1", "setoption name Hash value 16"]
    for name, value in setopts:
        commands.append(f"setoption name {name} value {value}")
    commands.append("setoption name NNUEArch value false")
    commands.append("isready")
    pos = f"position fen {fen}"
    if moves:
        pos += " moves " + " ".join(moves)
    commands.append(pos)
    commands.append(f"go {limit}")

    proc = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
    out_lines, err_lines = [], []

    def reader(stream, sink):
        for line in stream:
            sink.append(line.rstrip("\n"))

    t_out = threading.Thread(target=reader, args=(proc.stdout, out_lines), daemon=True)
    t_err = threading.Thread(target=reader, args=(proc.stderr, err_lines), daemon=True)
    t_out.start()
    t_err.start()

    for command in commands:
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
    # Wait for bestmove, then quit.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(l.startswith("bestmove") for l in out_lines):
            break
        time.sleep(0.02)
    proc.stdin.write("quit\n")
    proc.stdin.flush()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    t_out.join(timeout=5)
    t_err.join(timeout=5)
    return out_lines, err_lines


def main():
    engine = sys.argv[1]
    fen = sys.argv[2]
    moves = []
    limit = "depth 4"
    setopts = []
    args = sys.argv[3:]
    i = 0
    saw_dash = False
    while i < len(args):
        if args[i] == "--":
            saw_dash = True
            i += 1
            continue
        if saw_dash:
            if args[i] == "go":
                limit = args[i + 1]
                i += 2
                continue
            if args[i] == "--setopt":
                k, v = args[i + 1].split("=", 1)
                setopts.append((k, v))
                i += 2
                continue
            i += 1
        else:
            moves.append(args[i])
            i += 1
    import os
    env = dict(os.environ)
    out, err = run(engine, fen, moves, limit, setopts, env)
    print("=== stdout (search output) ===")
    for line in out:
        print(line)
    print("=== stderr (TRACE lines) ===")
    for line in err:
        print(line)


if __name__ == "__main__":
    main()
