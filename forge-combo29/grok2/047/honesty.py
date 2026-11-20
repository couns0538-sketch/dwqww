#!/usr/bin/env python3
"""Fresh-process honesty checks. No setoption. One process per command."""
import hashlib
import subprocess
import sys
from pathlib import Path

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_until(proc, lines, ok):
    while True:
        line = proc.stdout.readline()
        if line == "":
            sys.exit("STOP: engine closed stdout")
        line = line.rstrip("\r\n")
        lines.append(line)
        for token in BAD:
            if token in line:
                sys.exit(f"STOP: {line}")
        if ok(line):
            return line


def run_one(exe, command, out_path, meta_path):
    exe = str(Path(exe).resolve())
    digest = sha256_file(exe)
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines = []
    id_name = ""
    try:
        proc.stdin.write("uci\n")
        proc.stdin.flush()

        def capture(line):
            nonlocal id_name
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            return "uciok" in line

        read_until(proc, lines, capture)
        proc.stdin.write("isready\n")
        proc.stdin.flush()
        read_until(proc, lines, lambda line: line == "readyok")
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
        if command.startswith("bench"):
            read_until(proc, lines, lambda line: line.startswith("info string bench depth "))
        elif command.startswith("go perft"):
            read_until(proc, lines, lambda line: line.startswith("nodes "))
        else:
            sys.exit(f"STOP: unsupported command {command}")
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.wait(timeout=300)
    finally:
        if proc.poll() is None:
            proc.kill()
    out_path = Path(out_path)
    meta_path = Path(meta_path)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    meta = [
        f"exe: {exe}",
        f"sha256: {digest}",
        f"id name: {id_name}",
        "options:",
        f"command: {command}",
    ]
    meta_path.write_text("\n".join(meta) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")


def main():
    if len(sys.argv) != 5:
        sys.exit("usage: honesty.py EXE COMMAND OUT META")
    run_one(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
