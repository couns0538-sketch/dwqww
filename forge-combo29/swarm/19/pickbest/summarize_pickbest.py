#!/usr/bin/env python3
"""summarize_pickbest.py : prints the counter ratios that REPORT_pick_best.md quotes, from the raw counter
files. Every percentage in the report comes from this script's output; nothing is typed by hand.
"""
import re
import sys

FILES = [("bench 13", "counters_bench13.txt"), ("R_1911 depth 12 x200", "counters_R1911.err")]
PAT = re.compile(r"calls=(\d+) seeded=(\d+) partial=(\d+) sort=(\d+) scanned=(\d+) root=(\d+) quiet_score=(\d+)")

print("| quantity | " + " | ".join(name for name, _ in FILES) + " |")
print("|---|" + "---|" * len(FILES))
rows = {}
for name, path in FILES:
    body = open(path).read()
    m = PAT.search(body)
    if not m:
        print("COUNTER LINE NOT FOUND in " + path)
        sys.exit(1)
    rows[name] = [int(x) for x in m.groups()]

calls = {n: v[0] for n, v in rows.items()}


def row(label, fn):
    print("| %s | %s |" % (label, " | ".join(fn(n) for n, _ in FILES)))


row("`pick_best` calls", lambda n: "{:,}".format(rows[n][0]))
row("returned the seed", lambda n: "{:,} = **{:.1f} %**".format(rows[n][1], 100 * rows[n][1] / calls[n]))
row("partial-selection branch", lambda n: "{:,} = **{:.1f} %**".format(rows[n][2], 100 * rows[n][2] / calls[n]))
row("`std::sort` branch", lambda n: "{:,} = **{:.1f} %**".format(rows[n][3], 100 * rows[n][3] / calls[n]))
row("elements scanned", lambda n: "{:,} (**{:.1f}/call**)".format(rows[n][4], rows[n][4] / calls[n]))
row("scanned per NON-SEEDED partial call",
    lambda n: "{:.1f}".format(rows[n][4] / max(1, rows[n][2] - rows[n][1])))
row("calls from the root", lambda n: "{:,} = **{:.3f} %**".format(rows[n][5], 100 * rows[n][5] / calls[n]))
row("`QuietScorer::score` calls", lambda n: "{:,} (**{:.2f}/pick_best**)".format(rows[n][6], rows[n][6] / calls[n]))
