#!/usr/bin/env python3
"""Print the new option lines from a raw UCI honesty file."""

import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
for line in text.splitlines():
    if "IdeaS36" in line and line.startswith("option name "):
        print(line)
