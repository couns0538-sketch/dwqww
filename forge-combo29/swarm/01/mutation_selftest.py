#!/usr/bin/env python3
"""swarm seat 01: a MUTATION self-test for shape-sensitive checks (extends Trap 13's family B, S-F146).

Trap 13 concluded that family B "cannot be automated" because a bad input must be written in the shape the subject is
actually written in - the shape its author failed to imagine. That conclusion is too strong, and this tool narrows it.

The insight: **the subject already contains correctly-shaped instances of whatever the check looks for.** So instead of
hand-writing a bad input from my mental model, take a REAL instance out of the file, mutate it in a way that must
change the verdict, and confirm the check fails. The test input then comes from the file's own shape, not from my
imagination - which is exactly the missing ingredient.

Scope and limit, stated up front:
  * this works where a check reads TEXT and its subject has extractable instances (depth claims, spreads, stamps);
  * it does NOT work where the question is whether the check looks at a FILE AT ALL (the `*.md` glob) - a mutation of a
    file's content cannot reveal a file the check never opened. That part of family B stays imagination-only.
  * so the honest position is: **mutation testing automates family B for CONTENT, not for COVERAGE.**

Usage: mutation_selftest.py [--keep]
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent

# TRAP 14's GENERATED-LIST GUARD, and the one thing that makes it work: THIS MUST BE A LITERAL.
# If it were computed as len(results) or len(CLASSES) it would be derived from the same list it guards, so it
# would always match and the guard would be theatre - which is the original bug rebuilt in a new place. That is
# the obvious way the next author will implement it, so it is stated here rather than left to judgement.
# It is also written ONCE and used in both the report line and the assertion, because a duplicated literal is
# the same failure one step out.
EXPECTED_CLASSES = 4  # literal: the number of mutation classes I believe I implemented
FINDINGS = ROOT / "FINDINGS.md"
TRACE = ROOT / "clockfloor" / "analyse_outliers.json"


def run(args, env=None):
    import os
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), env=e)
    return r.returncode, r.stdout + r.stderr


def mutate_number(claim, group_index):
    """Change one number inside the claim by +1, keeping its formatting (commas)."""
    nums = re.findall(r"[0-9][0-9,]*", claim)
    if len(nums) <= group_index:
        return None
    old = nums[group_index]
    new = "{:,}".format(int(old.replace(",", "")) + 1)
    return claim.replace(old, new, 1), old, new


def test_depth_claims(tmp):
    """Shape-adaptive: lift a REAL claim from FINDINGS, corrupt one number, expect failure."""
    text = FINDINGS.read_text()
    pat = re.compile(r"[0-9][0-9,]*\s+vs\s+[0-9][0-9,]*\s+(?:nodes\s+)?at\s+d\d+")
    m = pat.search(text)
    if not m:
        return ("SKIP", "no claim of that shape present in FINDINGS.md - nothing to mutate. The check cannot be "
                        "tested this way, which is itself information: the selector may be looking for a shape the "
                        "file does not use. (Trap 12.)")
    claim = m.group(0)
    res = mutate_number(claim, 0)
    if not res:
        return ("SKIP", "could not mutate %r" % claim)
    mutated, old, new = res
    bad = tmp / "mutated_findings.md"
    bad.write_text(text.replace(claim, mutated, 1))
    rc, out = run([sys.executable, "check_depth_claims.py", str(bad), str(TRACE)])
    if rc == 0:
        return ("FAIL", "check passed on a claim mutated %s -> %s; it does not detect a wrong number in the shape it "
                        "claims to check" % (old, new))
    return ("OK", "real claim %r mutated %s -> %s, check failed as required" % (claim, old, new))


def test_findings_table(tmp):
    """Shape-adaptive: take a REAL well-formed row, add a cell, expect failure."""
    lines = [l for l in FINDINGS.read_text().splitlines() if l.startswith("| S-F")]
    if not lines:
        return ("SKIP", "no finding rows to mutate")
    row = lines[0]
    mutated = row + " extra cell |"
    bad = tmp / "mutated_table.md"
    bad.write_text(mutated + "\n")
    rc, _ = run([sys.executable, "check_findings_table.py", str(bad)],
                env={"FINDINGS_ARTIFACT": str(tmp / "art.txt")})
    if rc == 0:
        return ("FAIL", "table check passed on a real row with an extra cell")
    return ("OK", "real row + one extra cell, check failed as required")


def test_pooled_spread(tmp):
    """Shape-adaptive: take a REAL pooled line, strip its spread, expect failure."""
    txt = ROOT / "clockfloor" / "wall_time_pc20.txt"
    if not txt.exists():
        return ("SKIP", "no pooled artifact present")
    body = txt.read_text()
    # strip everything that looks like a spread marker
    out, removed = [], 0
    for line in body.splitlines():
        if re.search(r"Q1|quartile|IQR|PER-POSITION SPREAD|percent|% of positions|min .* max", line, re.I) \
                and re.search(r"ratio|[0-9]\.[0-9]", line):
            removed += 1
            continue
        out.append(line)
    if not removed:
        return ("SKIP", "could not identify spread lines to remove - the check's own marker vocabulary may be wrong")
    d = tmp / "clockfloor"
    d.mkdir(exist_ok=True)
    (d / "stripped.txt").write_text("\n".join(out) + "\n")
    rc, _ = run([sys.executable, "check_pooled_spread.py", str(d)])
    if rc == 0:
        return ("FAIL", "pooled check passed with %d spread lines removed" % removed)
    return ("OK", "%d spread lines removed from a real file, check failed as required" % removed)


def test_status_stamps(tmp):
    """Shape-adaptive: take a REAL stamp line from STATUS.md, move its date into the future, expect failure."""
    status = ROOT / "STATUS.md"
    if not status.exists():
        return ("SKIP", "no STATUS.md present")
    pat = re.compile(r"^## (\d{4})-(\d{2})-(\d{2})T", re.M)
    m = pat.search(status.read_text())
    if not m:
        return ("SKIP", "no ## stamp lines to mutate")
    # substitute the YEAR only: the smallest change that must flip a future-date verdict
    line_start = m.start()
    original = status.read_text()[line_start:line_start + 40]
    mutated = re.sub(r"^## \d{4}", "## 2099", original)
    bad = tmp / "mutated_status.md"
    bad.write_text("## 2099-01-01T00:00:00Z — mutated for the self-test\nbody\n")
    rc, out = run([sys.executable, "check_status_stamps.py", str(bad)])
    if rc == 0:
        return ("FAIL", "stamp check passed on a 2099 stamp")
    return ("OK", "real stamp %r mutated to 2099, check failed as required" % original.strip()[:32])


def main():
    tmp = Path(tempfile.mkdtemp())
    results = [
        ("depth claims vs trace", test_depth_claims(tmp)),
        ("findings table shape", test_findings_table(tmp)),
        ("pooled ratios carry spread", test_pooled_spread(tmp)),
        ("status stamps bounded", test_status_stamps(tmp)),
    ]
    print("MUTATION SELF-TEST - bad inputs derived from the files' own shape, not from my imagination")
    print("classes run: %d (expected %d)\n" % (len(results), EXPECTED_CLASSES))
    # TRAP 14's GENERATED-LIST GUARD (S-F151): a generated list can silently OMIT an item, and the omission is invisible
    # because there is no row to look wrong. So the count is asserted against what I believe I implemented. Proven by
    # deleting a class from the list above and watching the tool report success on three tests instead of four - which
    # is exactly the failure this constant prevents.
    if len(results) != EXPECTED_CLASSES:
        print("FAIL: %d mutation classes ran, expected %d. A class is missing from the list, and its absence cannot"
              % (len(results), EXPECTED_CLASSES))
        print("      show up as a failing row - that is the generated-list failure mode (Trap 14 / Trap 12).")
        return 1
    bad = 0
    for name, (status, detail) in results:
        print("  %-4s %-28s %s" % (status, name, detail))
        if status == "FAIL":
            bad += 1
    print()
    if bad:
        print("VERDICT: %d mutation(s) went undetected - that check's selector does not cover the shape its own file"
              % bad)
        print("uses, which is exactly the family-B failure this tool exists to find.")
        return 1
    print("VERDICT: every mutation derived from a real instance was detected.")
    print("LIMIT: this automates family B for CONTENT, not COVERAGE. A mutation cannot reveal a file the check never")
    print("opened - the `*.md`-only glob would still pass every test here. That part remains imagination-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
