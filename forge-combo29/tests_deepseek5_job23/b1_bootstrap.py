#!/usr/bin/env python3
"""job23 B1: the sum-ratio bootstrap over positions, 4,000 resamples, seed 2301. Prints the table."""
import json, random
D = "/agent/repos/dwqww/forge-combo29/tests_deepseek5_job23"
def nodes(fn):
    out = {}
    for ln in open(f"{D}/{fn}"):
        p = ln.strip().split("|")
        if len(p) >= 3 and p[0].isdigit():
            out[int(p[0])] = int(p[2])
    return out
base = nodes("none_set_G.epd_d12.rows")
print("ratio / 95% interval over POSITIONS (4,000 resamples, seed 2301), set G depth 12:")
for tag, fn in [("limit64", "DoubleExtLimit+64_set_G.epd_d12.rows"), ("limit10", "DoubleExtLimit+10_set_G.epd_d12.rows"),
                ("limit3", "DoubleExtLimit+3_set_G.epd_d12.rows"), ("limit1", "DoubleExtLimit+1_set_G.epd_d12.rows"),
                ("limit0", "DoubleExtLimit+0_set_G.epd_d12.rows"), ("limit-1", "DoubleExtLimit+-1_set_G.epd_d12.rows"),
                ("margin0", "DoubleExtMargin+0_set_G.epd_d12.rows"), ("margin12", "DoubleExtMargin+12_set_G.epd_d12.rows"),
                ("margin48", "DoubleExtMargin+48_set_G.epd_d12.rows"), ("margin96", "DoubleExtMargin+96_set_G.epd_d12.rows")]:
    r = nodes(fn)
    pairs = [(r[i], base[i]) for i in sorted(set(base) & set(r)) if base[i] > 0]
    agg = sum(a for a, b in pairs) / sum(b for a, b in pairs)
    rng = random.Random(2301)
    bs = []
    for _ in range(4000):
        sa = sb = 0
        for _ in range(len(pairs)):
            a, b = pairs[rng.randrange(len(pairs))]
            sa += a; sb += b
        bs.append(sa / sb)
    bs.sort()
    print(f"{tag}: ratio {agg:.4f} pos-interval [{bs[99]:.4f}, {bs[3899]:.4f}]")
