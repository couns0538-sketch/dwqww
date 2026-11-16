#!/usr/bin/env python3
"""readkimi13.py -- parse kimi5's job-13 verdict table out of its report.

Usage: readkimi13.py REPORT.md [--json]
Reads only the 35-row table whose first column is a setting name, and prints one line
per row: "setting | value | c | claim" where claim is "dead" or "live", plus the
claim's interval text when kimi5 gave one. Nothing is typed by hand: this is the
source of every setting and step value that job 6's runner uses.
"""
import json
import re
import sys

ROW = re.compile(r"^\|\s*\*{0,2}([A-Z][A-Za-z0-9]+)\*{0,2}\s*\|\s*([0-9]+)(?:→([0-9]+))?\s*\|\s*([0-9]+)\s*\|")


def main():
    path = sys.argv[1]
    want_json = "--json" in sys.argv
    rows = []
    in_table = False
    for line in open(path, encoding="utf-8"):
        if line.startswith("| setting | value | c |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            if rows:
                break
            continue
        m = ROW.match(line)
        if not m:
            continue
        name = m.group(1)
        value = int(m.group(3)) if m.group(3) else int(m.group(2))
        step = int(m.group(4))
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        claim_cell = cells[-1]
        dead = "dead" in claim_cell.lower()
        interval = ""
        im = re.search(r"dead on \[([0-9]+),\s*([0-9]+)\]", claim_cell)
        if im:
            interval = "%s..%s" % (im.group(1), im.group(2))
        rows.append({"setting": name, "value": value, "step": step,
                     "claim": "dead" if dead else "live", "interval": interval,
                     "claim_text": claim_cell})
    if want_json:
        json.dump(rows, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for r in rows:
            print("%-26s | %5d | %4d | %-4s %s"
                  % (r["setting"], r["value"], r["step"], r["claim"], r["interval"]))
    print("# rows %d, dead %d, live %d"
          % (len(rows), sum(1 for r in rows if r["claim"] == "dead"),
             sum(1 for r in rows if r["claim"] == "live")), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
