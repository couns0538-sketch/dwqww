#!/usr/bin/env python3
"""Print the last fastchess Results block and the finished-game count."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
finished = text.count("Finished game ")
print(f"finished_game_lines={finished}")
marker = "Results of "
idx = text.rfind(marker)
if idx < 0:
    raise SystemExit("no results block")
block = text[idx:]
end = block.find("Finished match")
if end >= 0:
    block = block[:end]
print(block.rstrip())
