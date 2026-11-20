#!/usr/bin/env python3
"""Paste-ready honesty table from the raw bench/perft files."""
import pathlib
import re
d = pathlib.Path(__file__).resolve().parent
rows = [
    ("bench 11", "honesty_b_bench11.txt", 312866),
    ("bench 13", "honesty_b_bench13.txt", 862329),
    ("bench 16", "honesty_b_bench16.txt", 3024920),
    ("go perft 5", "honesty_b_perft5.txt", 4865609),
]
lines = ["command\texpected\tnodes\tmatch"]
ok = True
for cmd, name, expected in rows:
    text = (d / name).read_text(errors="replace")
    found = [int(n) for n in re.findall(r"nodes (\d+)", text)]
    nodes = found[-1] if found else -1
    match = nodes == expected
    ok = ok and match
    lines.append(f"{cmd}\t{expected}\t{nodes}\t{'yes' if match else 'NO'}")
lines.append("all_match\t" + ("yes" if ok else "NO"))
(d / "HONESTY_B.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
