#!/usr/bin/env python3
"""render28.py -- read tests_deepseek6_long28/table.txt and print the markdown table of
report section 4 (setting | end | O sum | O nodes-chg | O bm-chg | G sum | G nodes-chg |
G bm-chg | O/G direction), one row per data line of table.txt. Nothing is retyped."""
import sys

path = "/tmp/ds6_work/forge-combo29/tests_deepseek6_long28/table.txt"
lines = [l.rstrip("\n") for l in open(path) if l.strip()]
print("| setting | end | O sum | O nodes-chg | O bm-chg | G sum | G nodes-chg | G bm-chg | O/G direction |")
print("|---|---|---|---|---|---|---|---|---|")
for l in lines[1:]:
    f = [x.strip() for x in l.strip("|").split("|")]
    # f: setting, end, O sum, O ratio, O nodes-chg, O bm-chg, G sum, G ratio, G nodes-chg, G bm-chg, job1, match, direction
    setting, end, osum, _, onc, obc, gsum, _, gnc, gbc, _, _, direction = f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8], f[9], f[10], f[11], f[12]
    if setting == "NonPawnCorrection":
        # table.txt has two half-rows for the one setting: O half and G half
        if f[2]:
            print(f"| {setting} | {end} | {osum} | {onc} | {obc} | (see G row) | | | {direction.split()[0] if direction else ''} |")
        else:
            print(f"| {setting} | {end} | (see O row) | | | {gsum} | {gnc} | {gbc} | {direction} |")
        continue
    print(f"| {setting} | {end} | {osum} | {onc} | {obc} | {gsum} | {gnc} | {gbc} | {direction} |")
