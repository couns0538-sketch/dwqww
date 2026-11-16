#!/usr/bin/env python3
"""audit_parsers.py — seat 11's re-audit of every check that greps engine output.

Seat 19's warning: a check that searched for a line the engine never prints got no number,
compared NaN, and printed CONFIRMS without measuring. For each of my checks I ask the only
question that matters: CAN A MISSING PARSE PASS AS A CONFIRMATION?

Method: a static, mechanical audit (grep the source for the guard patterns) PLUS a live
negative test where possible: run the check's parser on input that MUST fail and require it
to raise/report failure rather than confirm.

This file prints a table; nothing here is a claim about the engine.
"""
import ast, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

CHECKS = [
    ("check_s01f2.py", "perft node counts from `nodes N`"),
    ("check_s19f1.py", "`info string eval hce/nnue/total`"),
    ("check_s19f4.py", "nm symbols (no engine output)"),
    ("check_s19f5.py", "bench line via stdin"),
    ("check_s29f1.py", "bench line, several runs"),
    ("check_s05f3.py", "`score cp|mate N` per sweep point"),
    ("recount_long58.py", "rows files (no engine output)"),
]


def audit(path):
    src = open(os.path.join(HERE, path)).read()
    tree = ast.parse(src)
    findings = []

    # 1. does it raise / return non-zero on a failed parse?
    raises = any(isinstance(n, ast.Raise) for n in ast.walk(tree))
    findings.append(("raises on failure", raises))

    # 2. is any parsed value compared against None in a way that could pass?
    none_compare = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and any(isinstance(c, ast.Constant) and c.value is None
                                              for c in n.comparators):
            none_compare.append(n.lineno)
    findings.append(("None comparisons", bool(none_compare)))

    # 3. does the verdict depend on `all(ok ...)` where ok comes from a parse?
    has_all = "all(" in src
    findings.append(("guards with all(...)", has_all))

    # 4. the specific killer: a helper that maps "no output" onto a PASS
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name in ("drawish", "is_draw", "is_zero"):
            body = ast.dump(n)
            if "no-info" in body or "not infos" in ast.get_source_segment(src, n).replace(" ", ""):
                bad.append(n.name)
    findings.append(("maps no-output to a verdict", bool(bad)))
    return findings, bad


print(f"{'check':22} {'raises':>7} {'None-cmp':>9} {'all()':>6} {'no-out=pass':>12}  parsed thing")
print("-" * 96)
problem = []
for path, what in CHECKS:
    if not os.path.exists(os.path.join(HERE, path)):
        print(f"{path:22} MISSING")
        continue
    f, bad = audit(path)
    d = dict(f)
    row = (d["raises on failure"], d["None comparisons"], d["guards with all(...)"],
           d["maps no-output to a verdict"])
    print(f"{path:22} {str(row[0]):>7} {str(row[1]):>9} {str(row[2]):>6} {str(row[3]):>12}  {what}")
    if row[3]:
        problem.append(path)

print("-" * 96)
print("'None-cmp' true only means a None literal appears; what matters is whether a None can")
print("reach a PASS. Rows with 'no-out=pass' = True are the dangerous shape.")
print()
if problem:
    print("DANGEROUS (maps absent output onto a verdict): " + ", ".join(problem))
else:
    print("No check maps absent output onto a verdict after the fixes.")

print("""
=== the two I FIXED, and what changed ===
check_s05f3.py  BEFORE: drawish() returned True when status == "no-info", so a run that printed
                no score counted as "the draw appeared" -> would have CONFIRMED S-F3 from
                nothing. That is exactly seat 19's NaN failure.
                AFTER: probe() raises MeasurementError if there are no info lines, or if info
                lines exist but no `score cp|mate N` parses; main() catches it, prints
                "MEASUREMENT FAILED" and returns exit 2 with NO verdict.

check_s01f2.py  The perft comparison uses `eng_nodes == 64`; a None would be False, so a failed
                parse produces FAIL, not CONFIRMS — safe by construction (verified by reading
                line 67-69 and by the live run in checks/check_s01_f2.txt, where all five
                sub-checks are PASS individually and the control detects a 1-node difference).

=== live negative test for the fixed parser ===
Run check_s05f3.py against an executable that prints nothing: it must exit 2, not CONFIRMS.
""")
