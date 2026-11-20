#!/usr/bin/env python3
"""Print the last fastchess result block from match_OG.out, colour codes removed."""
import re
from pathlib import Path

text = Path(__file__).with_name("match_OG.out").read_text(errors="replace")
text = re.sub(r"\x1b\[[0-9;]*m", "", text)
start = text.rfind("Results of ")
end = text.rfind("Finished match")
if start < 0 or end < start:
    raise SystemExit("result block missing")
block = text[start:end]
# Keep the Finished match line and the total-time line that follows it.
tail = text[end:].splitlines()
keep = tail[:2]
print(block.rstrip())
print("\n".join(keep))
