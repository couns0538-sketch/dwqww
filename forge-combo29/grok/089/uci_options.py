#!/usr/bin/env python3
"""Save the uci option list. Stops if the process dies before uciok."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=60)
out.write_text(proc.stdout)
sha = hashlib.sha256(exe.read_bytes()).hexdigest()
id_name = ""
for line in proc.stdout.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
meta = f"exe={exe}\nsha256={sha}\nid_name={id_name}\noptions_sent=none\nstdin='uci\\nquit\\n'\nreturncode={proc.returncode}\n"
if proc.stderr:
    meta += "stderr_begin\n" + proc.stderr + "stderr_end\n"
Path(str(out) + ".meta").write_text(meta)
wanted = [line for line in proc.stdout.splitlines() if "IdeaA8" in line]
print("\n".join(wanted) if wanted else "NO IdeaA8 LINES")
if "uciok" not in proc.stdout:
    raise SystemExit("no uciok")
