#!/usr/bin/env python3
"""Record the uci option list and the IdeaK7 lines."""
import hashlib
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
proc = subprocess.run(
    [str(exe)],
    input="uci\nquit\n",
    text=True,
    capture_output=True,
    timeout=30,
    check=False,
)
text = proc.stdout
(out_dir / "uci_options.txt").write_text(text)
digest = hashlib.sha256(exe.read_bytes()).hexdigest()
id_name = ""
hits = []
for line in text.splitlines():
    if line.startswith("id name "):
        id_name = line[len("id name ") :]
    if "IdeaK7" in line:
        hits.append(line)
(out_dir / "uci_options.meta").write_text(
    f"exe={exe}\nsha256={digest}\nid_name={id_name}\noptions_sent=\n"
)
(out_dir / "uci_ideak7.txt").write_text("\n".join(hits) + "\n")
print("\n".join(hits))
