#!/usr/bin/env python3
"""Print Elo, error, and game count from a fastchess result file."""
import re
import sys

def main():
    text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    elo = re.findall(r"(?<![A-Za-z])Elo:\s*([+-]?[0-9.]+)\s*\+/-\s*([+-]?[0-9.]+)", text)
    games = re.findall(r"Games:\s*(\d+)", text)
    if not elo or not games:
        print("FAIL no result")
        return 1
    value, err = elo[-1]
    print("elo %s err %s games %s" % (value, err, games[-1]))
    return 0

if __name__ == "__main__":
    sys.exit(main())
