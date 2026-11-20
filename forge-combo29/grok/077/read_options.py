#!/usr/bin/env python3
"""Print the IdeaS44 lines from a saved uci answer."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
found = [line for line in text.splitlines() if "IdeaS44" in line and line.startswith("option ")]
for line in found:
    print(line)
print(f"count {len(found)}")
