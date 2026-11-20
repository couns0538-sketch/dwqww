#!/usr/bin/env python3
"""Print the last fastchess Results block and count PGN games."""
import sys
from pathlib import Path

stdout = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
blocks = []
current = []
inside = False
for line in stdout:
    if line.startswith("Results of "):
        current = [line]
        inside = True
        continue
    if inside:
        current.append(line)
        if line.startswith("Finished match") or (line.startswith("---") and len(current) > 2):
            blocks.append(current)
            inside = False
            current = []
# The final block is the last "Results of" group before "Finished match".
text = "\n".join(stdout)
start = text.rfind("Results of ")
end = text.rfind("Finished match")
print(text[start:end].rstrip())
print("Finished match")
if len(sys.argv) > 2:
    pgn = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
    print(f"pgn_games={pgn.count('[Event ')}")
