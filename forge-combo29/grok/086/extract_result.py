#!/usr/bin/env python3
"""Print the last fastchess result block. Colour codes removed. Argument: the log path."""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
text = re.sub(r"\x1b\[[0-9;]*m", "", text)
start = text.rfind("Results of ")
end = text.rfind("Finished match")
if start < 0 or end < start:
    raise SystemExit("result block missing")
tail = text[end:].splitlines()[:2]
print(text[start:end].rstrip())
print("\n".join(tail))
