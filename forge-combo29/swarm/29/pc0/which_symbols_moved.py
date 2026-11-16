#!/usr/bin/env python3
"""Where does the instruction difference actually live? Compares the SIZE and INSTRUCTION COUNT of every function
that differs between an unpatched and a patched binary of the same tree, ranked by the size change.

This turns "the probe is inlined more expensively" into a measured statement about which symbols moved, and in which
direction, or shows plainly that the probe did not move at all.
"""
import subprocess
import sys

A, B = sys.argv[1], sys.argv[2]
LA = sys.argv[3] if len(sys.argv) > 3 else "A"
LB = sys.argv[4] if len(sys.argv) > 4 else "B"


def syms(path):
    out = subprocess.run(["nm", "-C", "--print-size", "--defined-only", path],
                         capture_output=True, text=True).stdout
    d = {}
    for line in out.splitlines():
        p = line.split(None, 3)
        if len(p) < 4:
            continue
        addr, size, typ, name = p
        if typ not in ("W", "T", "t", "w"):
            continue
        try:
            d[name] = int(size, 16)
        except ValueError:
            pass
    return d


da, db = syms(A), syms(B)


def insn_count(path, name):
    """Instructions in one function, via objdump over its own address range."""
    out = subprocess.run(["nm", "--print-size", "--defined-only", path],
                         capture_output=True, text=True).stdout
    key = None
    for line in out.splitlines():
        p = line.split(None, 3)
        if len(p) < 4:
            continue
        if name in p[3] or p[3] == name:
            key = (int(p[0], 16), int(p[1], 16))
            break
    if key is None:
        return None
    addr, size = key
    d = subprocess.run(["objdump", "-d", f"--start-address={addr}",
                        f"--stop-address={addr + size}", path],
                       capture_output=True, text=True).stdout
    import re
    return sum(1 for line in d.splitlines() if re.match(r'^\s+[0-9a-f]+:\s+(?:[0-9a-f]{2} )+\s*\S', line))


rows = []
for name in sorted(set(da) | set(db)):
    a = da.get(name, 0)
    b = db.get(name, 0)
    if a != b:
        rows.append((b - a, name, a, b))
rows.sort(reverse=True, key=lambda r: abs(r[0]))
print(f"{LA}: {len(da)} symbols   {LB}: {len(db)} symbols   differing: {len(rows)}")
print()
print(f"| delta bytes | {LA} bytes | {LB} bytes | symbol |")
print("|---|---|---|---|")
for d, name, a, b in rows[:14]:
    print(f"| {d:+d} | {a} | {b} | {name[:88]} |")

print()
print("=== probe_body specifically ===")
for name in da:
    if "probe_body" in name:
        print(f"  {name[:80]}: {LA} {da[name]} bytes -> {LB} {db.get(name,'MISSING')} bytes")
print()
print("=== Worker::search instruction counts ===")
for pat in ("Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)'2",
            "Worker::search(forge::Board&, forge::SearchStack*, int, int, int, bool)"):
    for lbl, p in ((LA, A), (LB, B)):
        for name in da if lbl == LA else db:
            if name.startswith(pat.split("'2")[0]) and (pat.endswith("'2") == name.endswith("'2")):
                n = insn_count(p, name)
                print(f"  {lbl:14s} {name[:70]:70s} insns {n}")
                break
