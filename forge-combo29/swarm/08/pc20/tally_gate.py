#!/usr/bin/env python3
"""tally_gate.py OUT — count the FINDINGS series from the file and compare against the last STATUS claim.

Why this exists: this seat over-reported its own checks count by four (said 30, file held 26) because the number was
incremented in prose. The scoreboard is a measurement and it drifts like one. This gate makes the tally GENERATED:

  - count rows matching each id series in FINDINGS.md,
  - read the most recent "Tally:" line in STATUS.md,
  - report any disagreement, and print the correct line to paste.

Exit code is non-zero when they disagree, so it can be run before any message that quotes a tally.

ARGUMENT ORDER: OUT first.
"""
import re
import sys
from pathlib import Path

OUT = sys.argv[1]
base = Path("..").resolve()
findings = (base / "FINDINGS.md").read_text(errors="ignore")
status = (base / "STATUS.md").read_text(errors="ignore")

SERIES = {
    "findings": r"^\| 08-F\d+ ",
    "checks/audits/plants": r"^\| 08-C\d+ ",
    "method lines": r"^\| 08-N\d+ ",
    "withdrawals": r"^\| 08-W\d+ ",
    "open leads": r"^\| 08-O\d+ ",
}

counts = {}
ids = {}
for name, pat in SERIES.items():
    rx = re.compile(pat, re.M)
    found = rx.findall(findings)
    counts[name] = len(found)
    ids[name] = sorted({re.match(r"^\| (08-[A-Z]+\d+)", m) and re.match(r"^\| (08-[A-Z]+\d+)", m).group(1)
                        for m in re.findall(r"^\| 08-[A-Z]+\d+ .*$", findings, re.M)
                        if re.match(r"^\| 08-[A-Z]+\d+", m) and
                        re.match(r"^\| (08-[A-Z]+)", m).group(1) ==
                        {"findings": "08-F", "checks/audits/plants": "08-C", "method lines": "08-N",
                         "withdrawals": "08-W", "open leads": "08-O"}[name]})

# the last "Tally:" line in STATUS
claims = re.findall(r"\*\*?(\d+) findings, (\d+) checks[^*\n]*?, (\d+) method lines, (\d+) withdrawals", status)
last_claim = claims[-1] if claims else None

out = []
def emit(s):
    out.append(s)
    print(s)

emit("## Tally gate — counts GENERATED from FINDINGS.md, compared against the last STATUS claim")
emit("")
emit("| series | count | ids |")
emit("|---|---|---|")
for name in SERIES:
    emit("| %s | **%d** | %s |" % (name, counts[name], ", ".join(ids[name])))

emit("")
emit("| quantity | value |")
emit("|---|---|")
emit("| last STATUS tally claim | %s |" %
     (("findings %s, checks %s, method lines %s, withdrawals %s" % last_claim) if last_claim else "none found"))

built = "%d/%d/%d/%d" % (counts["findings"], counts["checks/audits/plants"],
                         counts["method lines"], counts["withdrawals"])
claimed = "/".join(last_claim) if last_claim else None
emit("| **the correct tally (paste this)** | **%s** |" % built)
emit("| last claim as a compact string | %s |" % (claimed or "-"))
emit("")
if claimed is None:
    emit("**No tally claim found in STATUS** — nothing to compare, but the generated line above is authoritative.")
    ok = True
elif claimed == built:
    emit("**GATE PASSES**: the last STATUS tally equals the count in FINDINGS.md (%s)." % built)
    ok = True
else:
    emit("**GATE FAILS**: STATUS claims **%s**, the file holds **%s**. The file wins; paste the generated line."
         % (claimed, built))
    ok = False

emit("")
emit("## How to use it")
emit("")
emit("    python3 tally_gate.py /tmp/t.txt && echo OK")
emit("")
emit("Run before any message that quotes a tally. A non-zero exit means the prose has drifted from the file.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")

sys.exit(0 if ok else 1)
