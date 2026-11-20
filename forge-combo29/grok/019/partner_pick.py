#!/usr/bin/env python3
"""Pick the next seat with this idea that already has a branch."""
import subprocess
from pathlib import Path
seat = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
idea = (seat - 1) % 50 + 1
cycle = [f"{n:03d}" for n in (idea, idea + 50, idea + 100)]
out = subprocess.check_output(
    ["git", "ls-remote", "origin", "refs/heads/for-fable-and-opus/grok-*"],
    text=True,
)
have = set()
for line in out.splitlines():
    ref = line.split()[-1]
    if "/grok-" in ref:
        have.add(ref.rsplit("/grok-", 1)[-1])
mine = f"{seat:03d}"
order = cycle[cycle.index(mine) + 1 :] + cycle[: cycle.index(mine)]
partner = next((n for n in order if n in have), "none")
print(f"seat {mine} idea {idea} cycle {' '.join(cycle)}")
print(f"present {' '.join(n for n in cycle if n in have) or 'none'}")
print(f"partner {partner}")
