#!/usr/bin/env python3
"""Save the uci option list and the lines for the new options."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
out.write_text(proc.stdout)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()
id_name = ""
for line in proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
meta = Path(str(out) + ".meta")
meta.write_text(f"exe={exe}\nsha256={sha}\nid_name={id_name}\noptions_sent=none\ncommand=uci\n")
print(f"exe={exe}")
print(f"sha256={sha}")
print(f"id_name={id_name}")
for line in proc.stdout.splitlines():
    if "IdeaK8" in line:
        print(line)
