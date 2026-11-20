#!/usr/bin/env python3
"""Honesty check. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()

id_proc = subprocess.run(
    [str(exe)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=60,
    check=False,
)
(out_dir / "honesty_B_uci.txt").write_text(id_proc.stdout)
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
for tag, command, expect in checks:
    proc = subprocess.run(
        [str(exe)],
        input=command + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=300,
        check=False,
    )
    raw_path = out_dir / f"honesty_B_{tag}.txt"
    raw_path.write_text(proc.stdout)
    meta = (
        f"exe {exe}\n"
        f"sha256 {sha}\n"
        f"id name {id_name}\n"
        f"options\n"
        f"(none)\n"
        f"command {command}\n"
        f"expect_nodes {expect}\n"
        f"returncode {proc.returncode}\n"
    )
    (out_dir / f"honesty_B_{tag}.meta").write_text(meta)
    node_lines = [ln for ln in proc.stdout.splitlines() if "nodes" in ln]
    got = node_lines[-1] if node_lines else "NO NODES LINE"
    ok = expect in got
    summary.append(f"{tag} expect {expect} line {got} ok {ok} rc {proc.returncode}")
    print(summary[-1], flush=True)

text = "\n".join(summary) + "\n"
(out_dir / "HONESTY_B.txt").write_text(text)
print(text, end="")
if any(" ok False" in line for line in summary):
    sys.exit(1)
