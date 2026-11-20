#!/usr/bin/env python3
"""Honesty check: one fresh engine process per command, no setoption."""
import hashlib
import queue
import subprocess
import threading
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
EXES = {
    "B": "/tmp/build-b/forge",
    "P": "/tmp/build-p/forge",
}
COMMANDS = [
    ("bench11", "bench 11", "info string bench "),
    ("bench13", "bench 13", "info string bench "),
    ("bench16", "bench 16", "info string bench "),
    ("perft5", "go perft 5", "nodes "),
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def open_engine(exe):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    lines_q = queue.Queue()

    def reader():
        try:
            for raw in proc.stdout:
                lines_q.put(raw)
        finally:
            lines_q.put(None)

    threading.Thread(target=reader, daemon=True).start()
    return proc, lines_q


def take_line(proc, lines_q, seconds):
    try:
        raw = lines_q.get(timeout=seconds)
    except queue.Empty:
        proc.kill()
        raise SystemExit("STOP timeout")
    if raw is None:
        proc.kill()
        raise SystemExit("STOP eof")
    line = raw.rstrip("\r\n")
    if any(b in line for b in BAD):
        proc.kill()
        raise SystemExit("STOP " + line)
    return line


def run_one(tag, exe, stem, command, sentinel):
    proc, lines_q = open_engine(exe)
    lines = []
    try:
        proc.stdin.write("uci\n")
        proc.stdin.flush()
        while True:
            line = take_line(proc, lines_q, 30)
            lines.append(line)
            if line == "uciok":
                break
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
        while True:
            line = take_line(proc, lines_q, 180)
            lines.append(line)
            if line.startswith(sentinel):
                break
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        proc.stdin.close()
        while True:
            try:
                raw = lines_q.get(timeout=10)
            except queue.Empty:
                break
            if raw is None:
                break
            lines.append(raw.rstrip("\r\n"))
        proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
    out = OUT / f"honesty_{tag}_{stem}.txt"
    meta = OUT / f"honesty_{tag}_{stem}.meta"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    id_name = ""
    for line in lines:
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    meta.write_text(
        f"exe: {exe}\nsha256: {sha256(exe)}\nid_name: {id_name}\ncommand: {command}\noptions_sent:\n",
        encoding="utf-8",
    )
    print(f"{tag} {command}: {lines[-1] if lines else 'EMPTY'}", flush=True)


def main():
    for tag, exe in EXES.items():
        for stem, command, sentinel in COMMANDS:
            run_one(tag, exe, stem, command, sentinel)


if __name__ == "__main__":
    main()
