#!/usr/bin/env python3
"""readkimi5.py -- read kimi5's job-5 rows json files into a comparable table.

Usage: readkimi5.py FILE.json [FILE.json ...]
Prints one line per file: "config | setopts | depth | n | sum | first3" so the settings
kimi5 actually ran (not merely described) are known before I reproduce them.
"""
import json
import sys


def main():
    for path in sys.argv[1:]:
        d = json.load(open(path))
        recs = d.get("records", [])
        s = sum(r["nodes"] for r in recs)
        first3 = " / ".join("%d" % r["nodes"] for r in recs[:3])
        print("%s | %s | d%s | n%d | sum %d | first3 %s"
              % (d.get("config", "?"), "; ".join(d.get("setopts", [])) or "(none)",
                 d.get("depth", "?"), len(recs), s, first3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
