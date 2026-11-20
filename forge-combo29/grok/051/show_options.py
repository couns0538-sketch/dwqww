#!/usr/bin/env python3
"""Print uci option lines for the idea from a raw uci transcript."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text().splitlines()
for line in text:
    if "option name IdeaE2" in line or "option name EvalRule50Damp" in line:
        print(line)
