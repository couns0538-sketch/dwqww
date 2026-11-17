#!/usr/bin/env python3
"""swarm seat 01: verify per-depth node claims in prose against the trace artifact (S-F136).

I typed "2,657 vs 2,075 at d7" into a finding row without ever reading those numbers. The real figures were
**12,657 vs 10,075**. That is Trap 0 — a hand-typed number beside a measured one, indistinguishable in the file —
and it is the second time tonight I have emitted a number I did not read (S-F132 was the first, in a different form).

The fix that has actually worked all session is to make the rule run. So this checks the narrow, checkable class:
**claims of the form "X vs Y at dN"** in the findings must match the per-depth node counts in the committed trace.
It cannot check every prose number — most have no machine-readable anchor — but this class does, and it is exactly
the class I got wrong.

Usage: check_depth_claims.py [FINDINGS.md] [trace.json]
Exit 1 on any mismatch, so it can gate a commit.
"""
import json
import re
import sys
from pathlib import Path

CLAIM = re.compile(r"([0-9][0-9,]*)\s+vs\s+([0-9][0-9,]*)\s+(?:nodes\s+)?at\s+d(\d+)")


def load_traces(path):
    """Build {depth: set(reported node counts)} over every position and setting in the trace artifact.

    A claim does not say WHICH position it came from, and in the row I was fixing it was a single position's two
    settings. So the check is membership: both numbers must appear, at that depth, somewhere in the artifact. That is
    weak, and deliberately so - it catches invented numbers, which is the failure I actually had. A wrong-but-present
    pairing would slip through, and the docstring says so rather than pretending otherwise.
    """
    d = json.load(open(path))
    by_depth = {}
    for rec in d.get("results", []):
        for side in ("s14", "pc20"):
            for it in rec.get(side, {}).get("iters", []):
                if "depth" in it and "nodes" in it:
                    by_depth.setdefault(it["depth"], set()).add(it["nodes"])
    return by_depth


def main():
    findings = Path(sys.argv[1] if len(sys.argv) > 1 else "FINDINGS.md")
    trace = Path(sys.argv[2] if len(sys.argv) > 2 else "clockfloor/analyse_outliers.json")
    if not trace.exists():
        print("SKIP: no trace artifact at %s" % trace)
        return 0
    by_depth = load_traces(trace)
    text = findings.read_text()
    # A claim inside a backtick span or a fenced block is QUOTED EVIDENCE - most often a wrong number being shown as
    # the error it was. My first version counted those and failed the gate on its own documentation, which is the
    # same false positive the escape check hit. Strip quoted regions before extracting claims.
    def strip_quoted(s):
        out, fenced = [], False
        for line in s.split("\n"):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                out.append("")
                continue
            if fenced:
                out.append("")
                continue
            # quoted evidence can be marked with backticks OR ordinary double quotes; prose uses both for
            # "the wrong number was X". Strip both before extracting claims.
            s = re.sub(r"`[^`]*`", "", line)
            s = re.sub(r'"[^"]*"', "", s)
            out.append(s)
        return "\n".join(out)
    hits = CLAIM.findall(strip_quoted(text))
    print("claims of the form 'X vs Y at dN': %d" % len(hits))
    bad = 0
    for a, b, dep in hits:
        ai, bi, di = int(a.replace(",", "")), int(b.replace(",", "")), int(dep)
        present = by_depth.get(di, set())
        ok_a, ok_b = ai in present, bi in present
        print("  %-9s vs %-9s at d%-3s %s" % (a, b, dep, "OK" if (ok_a and ok_b) else "NOT IN TRACE"))
        if not (ok_a and ok_b):
            bad += 1
            print("      depth %d has node counts %s" % (di, sorted(present)[:8]))
    if bad:
        print("\nVERDICT: %d claim(s) cite a node count that does not appear at that depth in the artifact." % bad)
        print("LIMIT: this checks membership, not pairing - a real number from the wrong position would pass.")
        return 1
    print("\nVERDICT: every per-depth node claim appears in the trace at that depth.")
    print("LIMIT: membership only. It catches invented numbers (my failure); it cannot catch a real number mis-paired.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
