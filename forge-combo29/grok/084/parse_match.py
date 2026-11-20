#!/usr/bin/env python3
"""Print the last fastchess results block and game counts. Usage: parse_match.py LOG PGN"""
import sys
from pathlib import Path

log = Path(sys.argv[1]).read_text(errors="replace")
start = log.rfind("Results of ")
print(log[start:].rstrip() if start >= 0 else "NO RESULTS BLOCK")
if len(sys.argv) > 2 and Path(sys.argv[2]).exists():
    pgn = Path(sys.argv[2]).read_text(errors="replace")
    results = []
    for line in pgn.splitlines():
        if line.startswith("[Result "):
            results.append(line.split('"')[1])
    draws = sum(1 for item in results if item == "1/2-1/2")
    print(f"pgn_games {len(results)}")
    print(f"pgn_draws {draws}")
    print(f"pgn_not_draws {len(results) - draws}")
