#!/usr/bin/env python3
"""Honesty check: one fresh engine process per command, no setoption.

Usage: python3 honesty.py <exe> <out-dir> <tag>
Writes <tag>_bench11.txt/.meta, bench13, bench16, perft5.
Prints one parsed nodes line per command.
"""
import hashlib
import queue
import subprocess
import sys
import threading
from pathlib import Path

STOP_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")
COMMANDS = (
    ("bench11", "bench 11", 312866),
    ("bench13", "bench 13", 862329),
    ("bench16", "bench 16", 3024920),
    ("perft5", "go perft 5", 4865609),
)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(exe, command, timeout):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines = []
    q = queue.Queue()

    def reader():
        for line in proc.stdout:
            q.put(line)
        q.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def read_line():
        try:
            item = q.get(timeout=timeout)
        except queue.Empty:
            proc.kill()
            raise SystemExit(f"STOP: timeout waiting for output after {command}")
        if item is None:
            raise SystemExit(f"STOP: engine closed stdout during {command}")
        line = item.rstrip("\n")
        lines.append(line)
        for marker in STOP_MARKERS:
            if marker in line:
                proc.kill()
                raise SystemExit(f"STOP: {line}")
        return line

    def send(text):
        proc.stdin.write(text + "\n")
        proc.stdin.flush()

    def until(pred):
        while True:
            if pred(read_line()):
                return

    id_name = ""
    send("uci")
    while True:
        line = read_line()
        if line.startswith("id name "):
            id_name = line[len("id name "):]
        if line == "uciok":
            break
    send("isready")
    until(lambda line: line == "readyok")
    send(command)
    if command.startswith("bench"):
        until(lambda line: line.startswith("info string bench depth "))
    else:
        # perft ends with a line that is exactly "nodes <N>"
        until(lambda line: line.startswith("nodes ") and line[6:].isdigit())
    send("quit")
    proc.wait(timeout=30)
    return lines, id_name


def nodes_of(tag, lines):
    if tag.startswith("bench"):
        for line in lines:
            if line.startswith("info string bench depth "):
                parts = line.split()
                return int(parts[parts.index("nodes") + 1])
    else:
        for line in reversed(lines):
            if line.startswith("nodes ") and line[6:].isdigit():
                return int(line.split()[1])
    raise SystemExit(f"STOP: no nodes line in {tag}")


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    exe = str(Path(sys.argv[1]).resolve())
    out_dir = Path(sys.argv[2])
    tag = sys.argv[3]
    digest = sha256_file(exe)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, command, expected in COMMANDS:
        lines, id_name = run_one(exe, command, timeout=180)
        stem = out_dir / f"honesty_{tag}_{name}"
        stem.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        meta = [
            f"exe={exe}",
            f"sha256={digest}",
            f"id_name={id_name}",
            "options:",
            f"command={command}",
        ]
        stem.with_suffix(".meta").write_text("\n".join(meta) + "\n", encoding="utf-8")
        got = nodes_of(name, lines)
        status = "OK" if got == expected else "MISS"
        print(f"{tag} {command} nodes {got} expected {expected} {status}")


if __name__ == "__main__":
    main()
