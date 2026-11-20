#!/usr/bin/env python3
"""Record the uci option list of one exe. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30)
text = proc.stdout
out.write_text(text)
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
id_name = ""
for line in text.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break
out.with_suffix(".meta").write_text(
    f"exe {exe}\nsha256 {digest}\nid_name {id_name}\noptions\ncommand uci\n"
)
for line in text.splitlines():
    if "IdeaS25" in line:
        print(line)
