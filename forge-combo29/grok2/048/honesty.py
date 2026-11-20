#!/usr/bin/env python3
"""honesty.py EXE OUTDIR PREFIX
Fresh engine process for each of bench 11, bench 13, bench 16, go perft 5.
No setoption. Raw stdout saved. .meta records the exe that was started.
id name comes from a separate process that is sent only "uci" then "quit".
"""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = sys.argv[1]
outdir = Path(sys.argv[2])
prefix = sys.argv[3]
outdir.mkdir(parents=True, exist_ok=True)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

digest = sha256(exe)
probe = subprocess.run([exe], input="uci\nquit\n", text=True, capture_output=True, timeout=60)
id_name = ""
for line in probe.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break
(outdir / f"honesty_{prefix}_uci.txt").write_text(probe.stdout)
if probe.stderr:
    (outdir / f"honesty_{prefix}_uci.txt").write_text(probe.stdout + "\n# stderr\n" + probe.stderr)

commands = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]
for tag, cmd in commands:
    proc = subprocess.run([exe], input=cmd + "\nquit\n", text=True, capture_output=True, timeout=300)
    raw = proc.stdout
    if proc.stderr:
        raw += "\n# stderr\n" + proc.stderr
    out = outdir / f"honesty_{prefix}_{tag}.txt"
    out.write_text(raw)
    meta = outdir / f"honesty_{prefix}_{tag}.meta"
    meta.write_text(
        "\n".join([
            f"exe {exe}",
            f"sha256 {digest}",
            f"id name {id_name}",
            f"command {cmd}",
            "options sent: none",
            "id name source: separate process, commands: uci ; quit",
            f"exit {proc.returncode}",
            "",
        ])
    )
    print(f"{prefix} {tag} exit={proc.returncode}")
    for line in raw.splitlines():
        if "nodes" in line:
            print(line)
