#!/usr/bin/env python3
"""Markdown table of nps_ab.py JSON results: one row per arm (B vs A), CPU-time NPS (primary) and engine NPS at each
depth as `pct [lo, hi]`, the speed rule (cpu lower bound >= +2 % at d16 and d20), and the PC busy share.
usage: nps_table.py <run.json> [<run.json> ...] [--title-col recipe]
"""
import json
import statistics
import sys


def cell(s):
    return f"{s['pct']:+.2f} [{s['lo']:+.2f}, {s['hi']:+.2f}]"


def main(paths):
    print("| run | arm (B vs A) | cpu d16 % | cpu d20 % | engine d16 % | engine d20 % | median cpu ratio d16 / d20 | rule |")
    print("|---|---|---|---|---|---|---|---|")
    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        a = next(x for x in data["arms"] if x["name"] == "A")
        busy = [r["pc_busy"] for r in data["runs"] if r["pc_busy"] == r["pc_busy"]]
        tag = f"{path.replace(chr(92), '/').split('/')[-1]} (A = {a['exe'].replace(chr(92), '/').split('/')[-1]}, " \
              f"core {data['args']['core']}, {data['args']['pairs']} pairs, PC busy {statistics.fmean(busy):.2f})"
        for row in data["summary"]:
            rule = "A/A control" if row["arm"] == "AA" else ("MET" if row.get("rule_met") else "not met")
            print(f"| {tag} | {row['arm']} | {cell(row['d16_nps_cpu'])} | {cell(row['d20_nps_cpu'])} | "
                  f"{cell(row['d16_nps_engine'])} | {cell(row['d20_nps_engine'])} | "
                  f"{row['d16_nps_cpu']['median_ratio']:.4f} / {row['d20_nps_cpu']['median_ratio']:.4f} | {rule} |")
            tag = ""


if __name__ == "__main__":
    main(sys.argv[1:])
