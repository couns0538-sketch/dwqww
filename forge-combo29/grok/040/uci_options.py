#!/usr/bin/env python3
"""Record the uci option list and check IdeaK1 defaults. No setoption."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = str(Path(sys.argv[1]).resolve())
out = Path(sys.argv[2])
proc = subprocess.run([exe], input="uci\nquit\n", text=True, capture_output=True, timeout=30, check=False)
raw = proc.stdout + (("\n" + proc.stderr) if proc.stderr else "")
out.write_text(raw)
digest = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
id_name = ""
for line in raw.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name "):]
        break
out.with_suffix(".meta").write_text(
    f"exe={exe}\nsha256={digest}\nid_name={id_name}\noptions=\ncommand=uci\nreturncode={proc.returncode}\n"
)
need = {
    "option name IdeaK1 type check default false": False,
    "option name IdeaK1_Margin type spin default 120 min 0 max 1000": False,
}
for line in raw.splitlines():
    if line in need:
        need[line] = True
for line, ok in need.items():
    print(("OK" if ok else "MISSING"), line)
sys.exit(0 if all(need.values()) else 1)
