#!/usr/bin/env python3
"""Record the uci identity and the IdeaS45 option lines."""
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1])
out = Path(sys.argv[2])
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, check=False)
text = proc.stdout
out.write_text(text)
wanted = ("IdeaS45", "IdeaS45_KingWorth", "IdeaS45_SeeMargin")
for line in text.splitlines():
    if line.startswith("id name ") or any(f"option name {name} " in line for name in wanted):
        print(line)
