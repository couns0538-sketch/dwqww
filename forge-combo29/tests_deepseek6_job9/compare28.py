#!/usr/bin/env python3
"""compare28.py -- read section 4 of REPORT_deepseek6_long28.md and the output of render28.py;
print every row that differs and the final 'N of M rows differ' line."""
import subprocess
import sys

REPORT = "/tmp/ds6_work/forge-combo29/REPORT_deepseek6_long28.md"

def end_norm(e):
    e = e.replace("\u2212", "-").strip()
    return {"-c": "m", "+c": "p"}.get(e, e)

def num(s):
    return s.replace(",", "").strip()

rep_lines = open(REPORT).read().splitlines()
i4 = next(i for i, l in enumerate(rep_lines) if l.startswith("## 4."))
i5 = next(i for i, l in enumerate(rep_lines) if l.startswith("## 5."))
rep_rows = []
for l in rep_lines[i4:i5]:
    if l.startswith("|") and not l.startswith("| setting") and not l.startswith("|---"):
        cells = [c.strip() for c in l.strip("|").split("|")]
        rep_rows.append(cells)

render = subprocess.run([sys.executable, "/tmp/ds6_work/forge-combo29/tests_deepseek6_job9/render28.py"],
                        capture_output=True, text=True).stdout.splitlines()
rrows = {}
for l in render:
    if l.startswith("|") and not l.startswith("| setting") and not l.startswith("|---"):
        cells = [c.strip() for c in l.strip("|").split("|")]
        rrows[(cells[0], cells[1])] = cells

diff = 0
total = 0
for cells in rep_rows:
    setting, end = cells[0], end_norm(cells[1])
    if setting == "CaptureFutilityMultiplier/Depth":
        subs = [("CaptureFutilityMultiplier", "m"), ("CaptureFutilityMultiplier", "p"),
                ("CaptureFutilityDepth", "m"), ("CaptureFutilityDepth", "p")]
    else:
        subs = [(setting, end)]
    if end not in ("m", "p"):
        print(f"NOTE (not counted): merged row {setting} {cells[1]} -- compare its halves in the render output")
        continue
    total += 1
    bad = []
    if setting == "CaptureFutilityMultiplier/Depth":
        # merged identity row: every sub-row must be the identity (O sum 9500069, 0 changes; G sum 18466239, 0 changes)
        for k in subs:
            r = rrows.get(k)
            if r is None:
                bad.append(f"missing {k}")
                continue
            if r[2] != "9500069" or r[3] != "0/200" or r[4] != "0/200" or r[5] != "18466239" or r[6] != "0/353" or r[7] != "0/353":
                bad.append(f"{k}: table is not the identity")
    else:
        r = rrows.get((setting, end))
        if r is None:
            bad.append("missing in render")
        else:
            def canon_dir(x):
                x = x.split("(")[0].strip()
                return {"FLIP": "flip", "SIGN-FLIP": "flip", "same": "same", "IDENTITY": "identity"}.get(x, x)
            for ci, ri in ((2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8)):
                cv = num(cells[ri]) if ri in (2, 5) else (canon_dir(cells[ri]) if ri == 8 else cells[ri])
                rv = canon_dir(r[ci]) if ci == 8 else r[ci]
                if cv != rv:
                    bad.append(f"col {ri}: report {cells[ri]!r} vs table {r[ci]!r}")
    if bad:
        diff += 1
        print(f"DIFFERS: {setting} {cells[1]}: " + "; ".join(bad))
print(f"{diff} of {total} rows differ")
