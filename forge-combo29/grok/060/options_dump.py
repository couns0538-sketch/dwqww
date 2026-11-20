#!/usr/bin/env python3
"""Save the uci option list. Usage: options_dump.py EXE OUTPREFIX"""
import hashlib
import os
import subprocess
import sys

def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main():
    exe = os.path.abspath(sys.argv[1])
    prefix = sys.argv[2]
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out, _ = proc.communicate("uci\nquit\n", timeout=30)
    with open(prefix + ".raw", "w", encoding="utf-8") as handle:
        handle.write(out)
    id_name = ""
    for line in out.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name ") :]
    with open(prefix + ".meta", "w", encoding="utf-8") as handle:
        handle.write("exe " + exe + "\n")
        handle.write("sha256 " + sha256(exe) + "\n")
        handle.write("id_name " + id_name + "\n")
        handle.write("options\n")
        handle.write("commands uci\n")
    shown = [line for line in out.splitlines() if "IdeaS24" in line]
    print("id_name", id_name)
    print("idea_lines", len(shown))
    for line in shown:
        print(line)

if __name__ == "__main__":
    main()
