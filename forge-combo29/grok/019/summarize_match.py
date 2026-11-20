#!/usr/bin/env python3
"""Print the fastchess result block and a game count from the log."""
from pathlib import Path
S = Path("/home/ubuntu/grok_seat.txt").read_text().strip()
d = Path("/home/ubuntu/grok_repo.txt").read_text().strip()
d = Path(d) / "forge-combo29" / "grok" / S
log = (d / "match_on_off.log").read_text(errors="replace").splitlines()
finished = sum(1 for ln in log if ln.startswith("Finished game "))
start = next(i for i, ln in enumerate(log) if ln.startswith("Results of "))
end = next(i for i, ln in enumerate(log) if ln.startswith("Finished match"))
block = log[start:end + 1]
print(f"finished_games {finished}")
print("\n".join(block))
