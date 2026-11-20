#!/usr/bin/env python3
"""Print the last fastchess results block from a match transcript."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else "match_og.txt"
text = (ROOT / name).read_text(encoding="utf-8", errors="replace").splitlines()
start = None
for index, line in enumerate(text):
    if line.startswith("Results of "):
        start = index
if start is None:
    print("NO_RESULTS")
    sys.exit(1)
end = len(text)
for index in range(start, len(text)):
    if text[index].startswith("Finished match"):
        end = index + 1
        break
sys.stdout.write("\n".join(text[start:end]) + "\n")
