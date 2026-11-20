#!/usr/bin/env python3
"""Honesty check: one fresh engine process per line, no setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()


def run(commands: list[str], timeout: int) -> tuple[str, str, int]:
    proc = subprocess.run(
        [str(exe)],
        input="\n".join(commands) + "\n",
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return proc.stdout, proc.stderr, proc.returncode


def write_meta(path: Path, command: str) -> None:
    lines = [
        f"exe: {exe}",
        f"sha256: {sha}",
        f"id_name: {id_name}",
        "id_name_from: honesty_b_uci.txt (separate process, uci then quit, no setoption)",
        "options_sent:",
        "(none)",
        f"command: {command}",
    ]
    path.write_text("\n".join(lines) + "\n")


uci_out, uci_err, uci_rc = run(["uci", "quit"], 30)
(out_dir / "honesty_b_uci.txt").write_text(uci_out)
if uci_err:
    (out_dir / "honesty_b_uci.err").write_text(uci_err)
id_name = ""
for line in uci_out.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break
write_meta(out_dir / "honesty_b_uci.meta", "uci")

jobs = [
    ("honesty_b_bench11.txt", ["bench 11", "quit"], "bench 11", 180),
    ("honesty_b_bench13.txt", ["bench 13", "quit"], "bench 13", 180),
    ("honesty_b_bench16.txt", ["bench 16", "quit"], "bench 16", 300),
    ("honesty_b_perft5.txt", ["go perft 5", "quit"], "go perft 5", 180),
]
rows = []
for name, cmds, command, timeout in jobs:
    stdout, stderr, rc = run(cmds, timeout)
    (out_dir / name).write_text(stdout)
    if stderr:
        (out_dir / (name + ".err")).write_text(stderr)
    write_meta(out_dir / (name + ".meta"), command)
    nodes = ""
    for line in stdout.splitlines():
        parts = line.split()
        if "nodes" in parts:
            nodes = parts[parts.index("nodes") + 1]
    rows.append(f"{command} nodes {nodes} rc {rc}")

(out_dir / "HONESTY_B.txt").write_text("\n".join(rows) + "\n")
print("\n".join(rows))
print(f"id_name {id_name}")
print(f"uci_rc {uci_rc}")
