#!/usr/bin/env python3
"""Honesty check for a named tag. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
tag = sys.argv[3]
out_dir.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()

id_proc = subprocess.run(
    [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60, check=False
)
(out_dir / f"honesty_{tag}_uci.txt").write_text(id_proc.stdout)
id_name = "MISSING"
for line in id_proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break

checks = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]
summary = [f"exe {exe}", f"sha256 {sha}", f"id name {id_name}"]
for name, command, expect in checks:
    proc = subprocess.run(
        [str(exe)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    (out_dir / f"honesty_{tag}_{name}.txt").write_text(proc.stdout)
    (out_dir / f"honesty_{tag}_{name}.meta").write_text(
        f"exe {exe}\nsha256 {sha}\nid name {id_name}\noptions\n(none)\n"
        f"command {command}\nexpect_nodes {expect}\nreturncode {proc.returncode}\n"
    )
    node_lines = [ln for ln in proc.stdout.splitlines() if "nodes" in ln]
    got = node_lines[-1] if node_lines else "NO NODES LINE"
    ok = expect in got
    summary.append(f"{name} expect {expect} line {got} ok {ok} rc {proc.returncode}")
    print(summary[-1], flush=True)
text = "\n".join(summary) + "\n"
(out_dir / f"HONESTY_{tag}.txt").write_text(text)
if any(" ok False" in line for line in summary):
    sys.exit(1)
