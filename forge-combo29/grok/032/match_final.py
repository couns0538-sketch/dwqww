#!/usr/bin/env python3
"""Print the last fastchess Results block from a log. That block is the match."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
marker = "Results of "
starts = [i for i in range(len(text)) if text.startswith(marker, i)]
if not starts:
    raise SystemExit("no results block")
block = text[starts[-1]:]
end = block.find("Finished match")
if end == -1:
    end = len(block)
print(block[:end].rstrip())
