#!/usr/bin/env python3
"""Print Elo, error, and game count from a fastchess result file."""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
elo = re.findall(r"^Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)", text, re.M)
games = re.findall(r"^Games:\s*(\d+),", text, re.M)
results = re.findall(r"^Results of .*$", text, re.M)
if not elo or not games:
    print("not done")
    sys.exit(1)
value, err = elo[-1]
print(f"elo={value}")
print(f"err={err}")
print(f"games={games[-1]}")
if results:
    print(results[-1])
