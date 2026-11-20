#!/usr/bin/env python3
"""Print the last 'Results of' block of a fastchess log, through 'Finished match'."""
import sys

lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
idxs = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not idxs:
    raise SystemExit("no results")
block = lines[idxs[-1]:]
end = next((i for i, line in enumerate(block) if line == "Finished match"), len(block) - 1)
print("\n".join(block[: end + 1]))
