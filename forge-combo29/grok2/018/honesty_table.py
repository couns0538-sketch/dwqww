#!/usr/bin/env python3
"""honesty_table.py OUTDIR
Print the node count from each honesty raw file. Reads the files; nothing is typed."""
import re
import sys
from pathlib import Path

out = Path(sys.argv[1])
wanted = {
    "bench11": 312866,
    "bench13": 862329,
    "bench16": 3024920,
    "perft5": 4865609,
}
ok = True
for name, expect in wanted.items():
    text = (out / f"{name}.txt").read_text(encoding="utf-8", errors="replace")
    nums = [int(n) for n in re.findall(r"nodes (\d+)", text)]
    got = nums[-1] if nums else None
    flag = "ok" if got == expect else "MISS"
    if flag != "ok":
        ok = False
    print(f"{name} nodes {got} expect {expect} {flag}")
print("honesty", "ok" if ok else "MISS")
sys.exit(0 if ok else 1)
