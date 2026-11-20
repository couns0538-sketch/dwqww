#!/usr/bin/env python3
"""Print the last fastchess Results block, including the Finished match line."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    sys.exit("no Results block")
start = starts[-1]
end = start
while end < len(lines) and lines[end] != "Finished match":
    end += 1
block = lines[start:end + 1]
if end + 1 < len(lines) and lines[end + 1].startswith("Total Time:"):
    block.append(lines[end + 1])
sys.stdout.write("\n".join(block) + "\n")
