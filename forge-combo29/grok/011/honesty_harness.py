#!/usr/bin/env python3
"""One fresh engine process per honesty line. No setoption."""
import hashlib, subprocess, sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
tag = sys.argv[3]
commands = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
out_dir.mkdir(parents=True, exist_ok=True)

def run_one(name, command):
    proc = subprocess.run(
        [str(exe)],
        input=f"uci\n{command}\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
    )
    raw = proc.stdout
    if proc.stderr:
        raw += "\n# stderr\n" + proc.stderr
    (out_dir / f"honesty_{tag}_{name}.txt").write_text(raw)
    id_name = ""
    for line in proc.stdout.splitlines():
        if line.startswith("id name "):
            id_name = line[len("id name "):]
            break
    meta = [
        f"exe {exe}",
        f"sha256 {digest}",
        f"id_name {id_name}",
        "options",
        f"command {command}",
    ]
    (out_dir / f"honesty_{tag}_{name}.meta").write_text("\n".join(meta) + "\n")
    nodes = None
    for line in proc.stdout.splitlines():
        if "nodes " in line:
            parts = line.replace(":", " ").split()
            if "nodes" in parts:
                nodes = parts[parts.index("nodes") + 1]
    print(f"{name} nodes={nodes} rc={proc.returncode}")

for name, command in commands:
    run_one(name, command)
