#!/usr/bin/env python3
"""aggchk.py -- sum a .chk file into a per-site made/breaches table.
Usage: aggchk.py CHKFILE -> prints 'site made breaches' lines sorted by site name."""
import sys
sites = {}
for line in open(sys.argv[1]):
    line = line.strip()
    if line.startswith("info string CHECK "):
        parts = line[len("info string CHECK "):].split()
        name, made, br = parts[0], int(parts[1]), int(parts[2])
        m, b = sites.get(name, (0, 0))
        sites[name] = (m + made, b + br)
    elif line.startswith("info string CHECKX"):
        pass
    elif line.startswith("info string CHECKFIRST"):
        pass
total_m = total_b = 0
for name in sorted(sites):
    m, b = sites[name]
    total_m += m
    total_b += b
    print(f"{name} {m} {b}")
print(f"TOTAL {total_m} {total_b}")
