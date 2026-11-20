#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption is sent.
The measured command is the first thing the process reads. `uci` is sent
after it, only so the transcript contains `id name`. Then `quit`.

  python3 honesty.py <exe> <out_dir> <tag>
Writes <tag>_bench11.txt, <tag>_bench13.txt, <tag>_bench16.txt, <tag>_perft5.txt
and a .meta file beside each.
"""
import hashlib
import os
import subprocess
import sys

COMMANDS = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def id_name(text):
    for line in text.splitlines():
        if line.startswith("id name "):
            return line[len("id name "):]
    return ""


def main():
    if len(sys.argv) != 4:
        sys.exit("usage: honesty.py <exe> <out_dir> <tag>")
    exe = os.path.abspath(sys.argv[1])
    out_dir = sys.argv[2]
    tag = sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    digest = sha256_file(exe)
    for suffix, command in COMMANDS:
        proc = subprocess.run(
            [exe],
            input=command + "\nuci\nquit\n",
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        text = proc.stdout
        if proc.stderr:
            text += proc.stderr
        out_path = os.path.join(out_dir, f"{tag}_{suffix}.txt")
        meta_path = os.path.join(out_dir, f"{tag}_{suffix}.meta")
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(text)
        name = id_name(text)
        with open(meta_path, "w", encoding="utf-8") as handle:
            handle.write(f"exe: {exe}\n")
            handle.write(f"sha256: {digest}\n")
            handle.write(f"id name: {name}\n")
            handle.write("options:\n")
            handle.write(f"first command: {command}\n")
            handle.write("setoption sent: none\n")
            handle.write(f"exit: {proc.returncode}\n")
        print(f"{suffix} bytes {len(text)} exit {proc.returncode} id {name}")
        if proc.returncode != 0:
            sys.exit(f"STOP: {command} exit {proc.returncode}")


if __name__ == "__main__":
    main()
