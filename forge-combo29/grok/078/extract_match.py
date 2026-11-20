#!/usr/bin/env python3
"""Print the last fastchess results block and the PGN game count."""
import sys
from pathlib import Path

folder = Path(__file__).resolve().parent
log = (folder / "match.log").read_text()
start = log.rfind("Results of ")
end = log.find("Finished match", start)
print(log[start:end].rstrip())
print("finished_match", "Finished match" in log)
pgn = (folder / "match.pgn").read_text(errors="replace")
print("pgn_games", pgn.count("[Event "))
print("pgn_results", pgn.count("[Result "))
