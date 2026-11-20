#!/usr/bin/env python3
"""Save the uci option list. No setoption."""
import subprocess
import sys
from pathlib import Path

exe = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
proc = subprocess.run([str(exe)], input="uci\nquit\n", text=True, capture_output=True, timeout=30)
text = proc.stdout
if proc.stderr:
    text += proc.stderr
out.write_text(text)
for line in text.splitlines():
    if "IdeaK6" in line:
        print(line)
