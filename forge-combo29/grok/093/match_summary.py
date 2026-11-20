#!/usr/bin/env python3
"""Print the last fastchess Results block from a match log."""
import pathlib
import sys

text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
starts = [i for i, line in enumerate(text) if line.startswith("Results of ")]
if not starts:
    print("no results")
    sys.exit(1)
block = []
for line in text[starts[-1] :]:
    if line.startswith("Finished match") or line.startswith("EXIT:"):
        break
    block.append(line)
    if line.startswith("-----") and len(block) > 1:
        break
print("\n".join(block))
