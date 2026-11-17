"""Assert the delivered folder is complete and self-consistent.

A missing evidence file turns a reproducible claim into an unbacked one, and the
absence is silent: the report still reads correctly. So the set is enumerated and
counted rather than assumed (forge-findings.md 6: "assert the exact expected
count, not a minimum").

Exits 1 on any missing file, any empty file, or any probe script with no
syntax-check pass.
"""

import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVIDENCE = os.path.join(ROOT, "evidence")

REQUIRED_TOP = ["FINDINGS.md", "STATUS.md", "README.md"]
REQUIRED_SCRIPTS = [
    "uci_driver.py",
    "probe_ponder.py",
    "probe_ponder2.py",
    "probe_ponder3.py",
    "probe_ponder4.py",
    "probe_ponder5_desync.py",
    "probe_ponder6_residuals.py",
    "probe_ponder7_suffix.py",
    "probe_ponder8_hazard.py",
    "probe_ponder9_bound.py",
    "make_tables.py",
    "check_claims.py",
]
REQUIRED_EVIDENCE = [
    "pins/pins.txt",
    "probe_results.json",
    "probe2_results.json",
    "probe3_results.json",
    "probe4_results.json",
    "probe5_results.json",
    "probe6_results.json",
    "probe7_results.json",
    "probe8_results.json",
    "probe9_results.json",
]

problems = []


def need(path, minimum_bytes=1):
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        problems.append(f"missing: {path}")
    elif os.path.getsize(full) < minimum_bytes:
        problems.append(f"empty or too small: {path} ({os.path.getsize(full)} bytes)")


for p in REQUIRED_TOP:
    need(p, 500)
for p in REQUIRED_SCRIPTS:
    need(os.path.join("scripts", p), 500)
for p in REQUIRED_EVIDENCE:
    need(os.path.join("evidence", p), 20)

# Every probe script must at least parse; a syntax error is a script nobody ran.
for p in REQUIRED_SCRIPTS:
    full = os.path.join(ROOT, "scripts", p)
    if not os.path.exists(full):
        continue
    try:
        ast.parse(open(full).read())
    except SyntaxError as exc:
        problems.append(f"syntax error in {p}: {exc}")

# Every evidence json must be valid and non-empty.
loaded = 0
for p in REQUIRED_EVIDENCE:
    if not p.endswith(".json"):
        continue
    full = os.path.join(ROOT, "evidence", p)
    if not os.path.exists(full):
        continue
    try:
        with open(full) as fh:
            data = json.load(fh)
        if not data:
            problems.append(f"empty json: {p}")
        else:
            loaded += 1
    except json.JSONDecodeError as exc:
        problems.append(f"invalid json in {p}: {exc}")

# The pins file must carry the four honesty pins, not just exist.
pins = os.path.join(EVIDENCE, "pins/pins.txt")
if os.path.exists(pins):
    text = open(pins).read()
    for pin in ("312866", "862329", "3024920", "4865609"):
        if pin not in text:
            problems.append(f"pin {pin} absent from evidence/pins/pins.txt")
    if "PINS MATCH" not in text:
        problems.append("evidence/pins/pins.txt does not record PINS MATCH")

print(f"checked {len(REQUIRED_TOP)} docs, {len(REQUIRED_SCRIPTS)} scripts, "
      f"{len(REQUIRED_EVIDENCE)} evidence files ({loaded} json parsed)")
if problems:
    for problem in problems:
        print("FAIL:", problem)
    sys.exit(1)
print("VERDICT: deliverable complete")
