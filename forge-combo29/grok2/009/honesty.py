#!/usr/bin/env python3
"""Honesty check: a fresh engine process per command, no setoption.

Usage: python3 honesty.py <exe> <tag> <outdir>
Writes <outdir>/honesty_<tag>_<name>.out and .meta
"""
import hashlib
import subprocess
import sys

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(exe, exe_sha, command, out_path, meta_path):
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

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        nonlocal id_name
        while True:
            line = proc.stdout.readline()
            if line == "":
                sys.exit(f"STOP: engine closed stdout during {command}")
            line = line.rstrip("\n")
            lines.append(line)
            low = line.lower()
            for token in STOP:
                if token.lower() in low:
                    open(out_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
                    sys.exit(f"STOP: {line}")
            if line.startswith("id name "):
                id_name = line[len("id name "):]
            if pred(line):
                return line

    send("uci")
    read_until(lambda line: line == "uciok")
    send("isready")
    read_until(lambda line: line == "readyok")
    send(command)
    if command.startswith("bench"):
        hit = read_until(lambda line: line.startswith("info string bench "))
    else:
        hit = read_until(lambda line: line.startswith("nodes "))
    send("quit")
    while True:
        line = proc.stdout.readline()
        if line == "":
            break
        lines.append(line.rstrip("\n"))
    rc = proc.wait(timeout=30)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(f"exe: {exe}\n")
        f.write(f"sha256: {exe_sha}\n")
        f.write(f"id name: {id_name}\n")
        f.write("options:\n")
        f.write("(none)\n")
        f.write(f"command: {command}\n")
        f.write(f"exit: {rc}\n")
    print(hit)
    return hit


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <tag> <outdir>")
    exe, tag, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    exe_sha = file_sha256(exe)
    commands = [
        ("bench11", "bench 11"),
        ("bench13", "bench 13"),
        ("bench16", "bench 16"),
        ("perft5", "go perft 5"),
    ]
    for name, command in commands:
        out_path = f"{outdir}/honesty_{tag}_{name}.out"
        meta_path = f"{outdir}/honesty_{tag}_{name}.meta"
        print(f"RUN {tag} {command}")
        run_one(exe, exe_sha, command, out_path, meta_path)


if __name__ == "__main__":
    main()
