#!/usr/bin/env python3
"""Read a fastchess log and print Elo, error, and game count from its summary."""
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
elo = re.findall(r"(?:^|\n)Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)", text)
games = re.findall(r"Games:\s*(\d+)", text)
if not elo or not games:
    print("elo missing")
    sys.exit(1)
value, err = elo[-1]
print(f"elo {value}")
print(f"err {err}")
print(f"games {games[-1]}")
low = float(value) - float(err)
high = float(value) + float(err)
print(f"interval {low} {high}")
print(f"whole_interval_below_0 {str(high < 0).lower()}")
print(f"below_minus_20 {str(float(value) < -20 and high < 0).lower()}")
