#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption.

Usage: honesty_run.py EXE OUTDIR LABEL
Writes bench11/bench13/bench16/perft5 raw text, a .meta beside each,
and LABEL (for example HONESTY_B.txt) as the concatenation of the raw files.
"""
import hashlib
import os
import subprocess
import sys

STOP = ("unknown option", "invalid value", "invalid FEN", "illegal move")
EXPECT = {
    "bench11": "nodes 312866",
    "bench13": "nodes 862329",
    "bench16": "nodes 3024920",
    "perft5": "nodes 4865609",
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(exe, commands, timeout):
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    payload = "\n".join(commands + ["quit"]) + "\n"
    try:
        out, _ = proc.communicate(payload, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        out += "\nTIMEOUT\n"
    for line in out.splitlines():
        if any(bad in line for bad in STOP):
            sys.stderr.write("STOP " + line + "\n")
            sys.exit(2)
    return out


def write_meta(path, exe, digest, id_name, commands):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("exe " + exe + "\n")
        handle.write("sha256 " + digest + "\n")
        handle.write("id_name " + id_name + "\n")
        handle.write("options\n")
        for command in commands:
            if command.startswith("setoption "):
                handle.write(command + "\n")
        handle.write("commands " + " | ".join(commands) + "\n")


def main():
    if len(sys.argv) != 4:
        sys.stderr.write("usage: honesty_run.py EXE OUTDIR LABEL\n")
        sys.exit(2)
    exe = os.path.abspath(sys.argv[1])
    outdir = sys.argv[2]
    label = sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    digest = sha256(exe)
    id_out = run(exe, ["uci"], 60)
    id_name = ""
    for line in id_out.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
            break
    jobs = [
        ("bench11", ["bench 11"], 180),
        ("bench13", ["bench 13"], 180),
        ("bench16", ["bench 16"], 300),
        ("perft5", ["go perft 5"], 180),
    ]
    parts = []
    failed = False
    for name, commands, timeout in jobs:
        out = run(exe, commands, timeout)
        raw_path = os.path.join(outdir, name + ".txt")
        with open(raw_path, "w", encoding="utf-8") as handle:
            handle.write(out)
        write_meta(os.path.join(outdir, name + ".meta"), exe, digest, id_name, commands)
        ok = EXPECT[name] in out
        if not ok:
            failed = True
        print(name, "PASS" if ok else "FAIL", flush=True)
        parts.append("===== " + name + " =====\n" + out)
        if not out.endswith("\n"):
            parts.append("\n")
    label_path = label if os.path.isabs(label) else os.path.join(outdir, label)
    with open(label_path, "w", encoding="utf-8") as handle:
        handle.write("".join(parts))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
