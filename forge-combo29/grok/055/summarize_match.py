#!/usr/bin/env python3
"""Print the fastchess result block and the PGN game count. Nothing is typed."""
import pathlib
import sys

folder = pathlib.Path(__file__).resolve().parent
log_name = sys.argv[1] if len(sys.argv) > 1 else "match_og.log"
pgn_name = sys.argv[2] if len(sys.argv) > 2 else "match_og.pgn"
log = (folder / log_name).read_text(errors="replace").splitlines()
start = None
for index, line in enumerate(log):
    if line.startswith("Results of "):
        start = index - 1 if index else 0
print("\n".join(log[start:] if start is not None else ["NO RESULTS BLOCK"]))
events = 0
for line in (folder / pgn_name).read_text(errors="replace").splitlines():
    if line.startswith("[Event "):
        events += 1
print(f"pgn_events {events}")
print(f"unknown_option {sum(1 for line in log if 'unknown option' in line.lower())}")
