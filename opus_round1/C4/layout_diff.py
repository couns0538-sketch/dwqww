#!/usr/bin/env python3
"""Which functions moved: compares two `objdump -d -C --no-show-raw-insn` listings by function name and
prints every forge function whose start address mod 64 or whose size (span to the next symbol) differs,
plus new and removed functions. usage: layout_diff.py <a.dis> <b.dis> [name-regex]"""
import re
import sys

sym = re.compile(r"^([0-9a-f]+) <(.*)>:$")


def layout(path):
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = sym.match(line.rstrip("\n"))
        if m:
            rows.append((int(m.group(1), 16), m.group(2)))
    out = {}
    for i, (addr, name) in enumerate(rows):
        span = rows[i + 1][0] - addr if i + 1 < len(rows) else 0
        out.setdefault(name, (addr, span))
    return out


a, b = layout(sys.argv[1]), layout(sys.argv[2])
pat = re.compile(sys.argv[3] if len(sys.argv) > 3 else r"forge::")
same = moved = 0
for name in sorted(set(a) | set(b), key=lambda n: (b.get(n, a.get(n))[0])):
    if not pat.search(name):
        continue
    if name not in a:
        print(f"NEW     mod64={b[name][0] % 64:2d} span={b[name][1]:6d}  {name[:130]}")
        continue
    if name not in b:
        print(f"REMOVED mod64={a[name][0] % 64:2d} span={a[name][1]:6d}  {name[:130]}")
        continue
    (aa, asz), (ba, bsz) = a[name], b[name]
    if aa % 64 != ba % 64 or asz != bsz:
        moved += 1
        print(f"CHANGED mod64 {aa % 64:2d}->{ba % 64:2d} span {asz:6d}->{bsz:6d} (delta addr {ba - aa:+#x})  {name[:110]}")
    else:
        same += 1
print(f"unchanged (same mod64 and span): {same}; changed: {moved}")
