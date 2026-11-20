#!/usr/bin/env python3
"""Save the uci option list and report IdeaS15 defaults."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
proc = subprocess.run(
    [str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60, check=False
)
raw = out_dir / "uci_P.txt"
raw.write_text(proc.stdout)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()
id_name = "MISSING"
for line in proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
(out_dir / "uci_P.meta").write_text(
    f"exe {exe}\nsha256 {sha}\nid name {id_name}\noptions\n(none)\ncommand uci\n"
)
wanted = {
    "option name IdeaS15 type check default false": False,
    "option name IdeaS15_MinPieces type spin default 8 min 2 max 32": False,
}
for line in proc.stdout.splitlines():
    if line in wanted:
        wanted[line] = True
for line, found in wanted.items():
    print(("found " if found else "MISSING ") + line)
if not all(wanted.values()):
    sys.exit(1)
