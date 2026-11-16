#!/usr/bin/env python3
"""audit_final.py : does the FINAL still present any WITHDRAWN finding as live?

The risk this guards against: I withdraw something in FINDINGS.md and forget to update the FINAL, so a top-down
reader acts on the old claim. This cross-checks every S-F id that FINDINGS.md marks WITHDRAWN / NOT A DEFECT /
REFUTED / COSMETIC against its row in STATUS.md and reports any mismatch.

It is a text cross-check, not a proof: it flags rows for a human to look at rather than deciding correctness.
"""
import pathlib
import re

STORE = pathlib.Path("/agent/repos/dwqww/forge-combo29/swarm/25")
findings = (STORE / "FINDINGS.md").read_text()
status = (STORE / "STATUS.md").read_text()

DEAD_MARKS = ("WITHDRAWN", "NOT A DEFECT", "REFUTED", "COSMETIC", "Superseded", "SETTLED", "closed")
LIVE_MARKS = ("NEW",)

# collect each finding id's status from FINDINGS.md
rows = {}
for line in findings.split("\n"):
    m = re.match(r"\| (S-[FC]\d+) \|", line)
    if not m:
        continue
    fid = m.group(1)
    # only look at the STATUS-bearing part: the LAST cell of the row, which is where I put the state.
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    status_cell = cells[-1] if cells else ""
    dead = [d for d in DEAD_MARKS if d.lower() in status_cell.lower()]
    rows[fid] = dead

# now check the FINAL's rows for the same ids
print(f"{'id':<8} {'FINDINGS status':<34} {'FINAL row says':<34} verdict")
print("-" * 104)
problems = 0
for fid, dead in sorted(rows.items(), key=lambda kv: (kv[0][2], int(kv[0][3:]))):
    if not dead:
        continue
    # find its row in STATUS.md
    final_line = None
    for l in status.split("\n"):
        if l.startswith(f"| {fid} |"):
            final_line = l
            break
    finding_status = ", ".join(dead)[:32]
    if final_line is None:
        print(f"{fid:<8} {finding_status:<34} {'(no row in FINAL)':<34} NOTE")
        continue
    fcells = [c.strip() for c in final_line.strip().strip("|").split("|")]
    fstatus = fcells[-1] if fcells else ""
    final_dead = [d for d in DEAD_MARKS if d.lower() in fstatus.lower()]
    # a FINAL row that states the disposition in its TEXT (not the status cell) also counts as consistent
    if not final_dead:
        ftext = " ".join(fcells[:-1])
        if any(d.lower() in ftext.lower() for d in DEAD_MARKS):
            final_dead = ["stated in row text"]
    if final_dead:
        verdict = "consistent"
    else:
        verdict = "MISMATCH - FINAL presents it as live"
        problems += 1
    print(f"{fid:<8} {finding_status:<34} {(', '.join(final_dead) or 'live')[:32]:<34} {verdict}")

print()
print(f"mismatches: {problems}")
if problems == 0:
    print("Every finding marked dead in FINDINGS.md is also marked dead in the FINAL.")
else:
    print("Fix the rows above before the FINAL is read top-down.")
