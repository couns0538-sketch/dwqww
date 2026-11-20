#!/usr/bin/env python3
"""Build HONESTY_B.txt from the raw honesty transcripts. Nothing is typed."""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent
parts = [
    ("bench11", "bench 11", "312866"),
    ("bench13", "bench 13", "862329"),
    ("bench16", "bench 16", "3024920"),
    ("perft5", "go perft 5", "4865609"),
]
out = []
out.append("exe_b=/agent/repos/base/forge-combo29/build/forge")
for tag, _cmd, _expect in parts:
    meta = (root / f"honesty_b_{tag}.meta").read_text()
    out.append(f"--- meta {tag} ---")
    out.append(meta.rstrip("\n"))
all_ok = True
for tag, cmd, expect in parts:
    raw = (root / f"honesty_b_{tag}.txt").read_text().splitlines()
    hit = ""
    for line in raw:
        if "bench depth" in line or line.startswith("nodes "):
            hit = line
    got = ""
    m = re.search(r"nodes (\d+)", hit)
    if m:
        got = m.group(1)
    ok = got == expect
    all_ok = all_ok and ok
    out.append(f"COMMAND {cmd}")
    out.append(f"LINE {hit}")
    out.append(f"GOT {got}")
    out.append(f"EXPECT {expect}")
    out.append(f"MATCH {ok}")
out.append(f"ALL_MATCH {all_ok}")
(root / "HONESTY_B.txt").write_text("\n".join(out) + "\n")
print("\n".join(out[-12:]))
