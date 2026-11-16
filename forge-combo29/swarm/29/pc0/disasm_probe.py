#!/usr/bin/env python3
"""Is the probe really re-inlined more expensively with my patch? MEASURED, not inferred from symbol sizes.

Method, per binary:
  1. `nm --print-size` gives each function's address and byte size.
  2. `objdump -d` over that address range gives its actual instructions.
  3. Count total instructions, and count specifically the instructions that implement the comparison work the
     patch touches: 32-bit compares against the verification key (`cmp ...`), the occupancy test, and (in the
     patched build) the SSE2 key compare (`pcmpeqd`), plus the lane scan.

Then the caller: count how many bytes of `Worker::search` are spent on `call`s into probe_body versus inline compare
sequences, so a claim about inlining can be checked rather than guessed.

Prints a table; every number is read from the binary, none typed.
"""
import re
import subprocess
import sys

BINS = [(sys.argv[3] if len(sys.argv) > 3 else "A", sys.argv[1]),
        (sys.argv[4] if len(sys.argv) > 4 else "B", sys.argv[2])]


def symbols(path):
    out = subprocess.run(["nm", "-C", "--print-size", "--defined-only", path],
                         capture_output=True, text=True).stdout
    syms = {}
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4:
            continue
        addr, size, _typ, name = parts
        try:
            syms[name] = (int(addr, 16), int(size, 16))
        except ValueError:
            continue
    return syms


def disasm(path, start, size):
    out = subprocess.run(["objdump", "-d", f"--start-address={start}",
                          f"--stop-address={start + size}", path],
                         capture_output=True, text=True).stdout
    insns = []
    for line in out.splitlines():
        m = re.match(r'^\s+([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(.*)$', line)
        if m:
            insns.append(m.group(2).strip())
    return insns


def find(syms, needle):
    for name, v in syms.items():
        if needle in name:
            return name, v
    return None, None


print("| binary | function | bytes | instructions | cmps | pcmpeqd | calls |")
print("|---|---|---|---|---|---|---|")
detail = {}
for label, path in BINS:
    syms = symbols(path)
    for pat in ("probe_body<true>", "probe_body<false>"):
        name, v = find(syms, pat)
        if v is None:
            print(f"| {label} | {pat} | MISSING | | | | |")
            continue
        addr, size = v
        ins = disasm(path, addr, size)
        cmps = sum(1 for i in ins if re.match(r'^cmp\b', i))
        pcmpeq = sum(1 for i in ins if 'pcmpeqd' in i)
        calls = sum(1 for i in ins if re.match(r'^call', i))
        detail[(label, pat)] = (size, len(ins), cmps, pcmpeq, calls)
        print(f"| {label} | {pat} | {size} | {len(ins)} | {cmps} | {pcmpeq} | {calls} |")

print()
print("=== per-call cost check: does the patched probe cost more instructions per CALL? ===")
# call counts come from the earlier callgrind runs (probe_body<false> is the hot one in search)
calls_base = 3  # placeholder, replaced below if callgrind data is available
print("instruction *counts* above are static (code size). The dynamic question needs call counts; see below.")
for pat in ("probe_body<true>", "probe_body<false>"):
    a = detail.get(("base PC", pat))
    b = detail.get(("patched", pat))
    if a and b:
        print(f"  {pat}: base {a[1]} insns / {a[0]} bytes   patched {b[1]} insns / {b[0]} bytes   "
              f"delta {b[1]-a[1]:+d} insns")
