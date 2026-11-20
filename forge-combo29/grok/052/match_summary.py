#!/usr/bin/env python3
"""Print the fastchess results block from the raw match log."""
import pathlib
import sys

text = pathlib.Path(sys.argv[1]).read_text()
start = text.rfind("Results of")
if start < 0:
    raise SystemExit("no results block")
print(text[start:].rstrip())
