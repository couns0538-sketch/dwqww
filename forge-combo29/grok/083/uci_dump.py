#!/usr/bin/env python3
"""Save the uci option list and a .meta for the exe that was started."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
prefix = sys.argv[3]
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
raw = out / f"{prefix}.txt"
raw.write_text(proc.stdout + (("\n# stderr\n" + proc.stderr) if proc.stderr else ""))
name = ""
for line in proc.stdout.splitlines():
    if line.startswith("id name "):
        name = line[len("id name ") :]
(out / f"{prefix}.meta").write_text(
    f"exe: {exe}\nsha256: {digest}\nid name: {name}\noptions sent:\n(none)\n"
)
for line in proc.stdout.splitlines():
    if "IdeaA2" in line or line.startswith("id name "):
        print(line)
