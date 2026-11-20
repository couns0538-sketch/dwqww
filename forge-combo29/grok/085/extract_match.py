#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
start = text.rfind("Results of ")
end = text.find("Finished match", start)
if start < 0 or end < 0:
    print("no results block")
    sys.exit(1)
print(text[start:end].rstrip())
print("Finished match")
