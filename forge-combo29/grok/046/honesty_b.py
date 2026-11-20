#!/usr/bin/env python3
"""Honesty check of exe B. One fresh process per line. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
digest = hashlib.sha256(exe.read_bytes()).hexdigest()

id_proc = subprocess.run(
    [str(exe)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=30,
    check=False,
)
id_text = id_proc.stdout
id_name = ""
for line in id_text.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
        break
(out_dir / "honesty_b_id.txt").write_text(id_text)

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
    raw_path = out_dir / f"honesty_b_{name}.txt"
    raw_path.write_text(text)
    meta = (
        f"exe={exe}\n"
        f"sha256={digest}\n"
        f"id_name={id_name}\n"
        f"options_sent=\n"
        f"stdin={cmd}\\nquit\\n\n"
        f"returncode={proc.returncode}\n"
    )
    (out_dir / f"honesty_b_{name}.meta").write_text(meta)
    print(f"{name} rc={proc.returncode}")
    for line in text.splitlines():
        if "nodes" in line:
            print(line)
