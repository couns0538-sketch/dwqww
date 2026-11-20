#!/usr/bin/env python3
"""Honesty check. Fresh process per line. No setoption. Prefix is the file stem."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
prefix = sys.argv[3]
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
id_proc = subprocess.run(
    [str(exe)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=30,
    check=False,
)
id_name = ""
for line in id_proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break
(out_dir / f"{prefix}_id.txt").write_text(id_proc.stdout)
commands = [
    ("bench11", "bench 11"),
    ("bench13", "bench 13"),
    ("bench16", "bench 16"),
    ("perft5", "go perft 5"),
]
for name, cmd in commands:
    proc = subprocess.run(
        [str(exe)],
        input=cmd + "\nquit\n",
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    text = proc.stdout
    if proc.stderr:
        text += "\n# stderr\n" + proc.stderr
    (out_dir / f"{prefix}_{name}.txt").write_text(text)
    (out_dir / f"{prefix}_{name}.meta").write_text(
        f"exe={exe}\nsha256={digest}\nid_name={id_name}\noptions_sent=\nstdin={cmd}\\nquit\\n\nreturncode={proc.returncode}\n"
    )
    print(f"{prefix} {name} rc={proc.returncode}")
    for line in text.splitlines():
        if "nodes" in line and (line.startswith("info string bench") or line.startswith("nodes ")):
            print(line)
