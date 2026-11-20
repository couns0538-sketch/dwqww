#!/usr/bin/env python3
"""Print Elo, error, and game count from a fastchess result file."""
import pathlib
import re
import sys

folder = pathlib.Path(__file__).resolve().parent
name = sys.argv[1] if len(sys.argv) > 1 else "match_og.txt"
text = (folder / name).read_text()
elos = re.findall(r"Elo:\s*([+-]?\d+(?:\.\d+)?)\s*\+/-\s*([+-]?\d+(?:\.\d+)?)", text)
games = re.findall(r"Games:\s*(\d+)", text)
if not elos or not games:
    print(f"{name} PARSE_FAIL")
    raise SystemExit(1)
elo_point, elo_err = elos[-1]
print(f"{name} elo {elo_point} err {elo_err} games {games[-1]}")
