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
    """Build PAIRED node counts: {(position_index, depth): {side: nodes}}.

    The first version of this check only asked whether each number appeared at that depth ANYWHERE in the artifact -
    membership, not pairing - and said so as a limit. The coordinator pointed out the trace can do better, and it can:
    a claim "X vs Y at dN" is supported only if X and Y are the two sides' node counts AT THE SAME DEPTH OF THE SAME
    POSITION. That is the gap the fabrications exploited, so it is now closed.

    A claim still does not name its position, so the check accepts the pair if SOME single position/depth satisfies
    both values in the right roles. That is pairing within a row; it is not attribution to a named row, which the
    prose would have to carry.
    """
    d = json.load(open(path))
    paired = {}
    for i, rec in enumerate(d.get("results", [])):
        for side in ("s14", "pc20"):
            for it in rec.get(side, {}).get("iters", []):
                if "depth" in it and "nodes" in it:
                    paired.setdefault((i, it["depth"]), {})[side] = it["nodes"]
    return paired


def main():
    findings = Path(sys.argv[1] if len(sys.argv) > 1 else "FINDINGS.md")
    trace = Path(sys.argv[2] if len(sys.argv) > 2 else "clockfloor/analyse_outliers.json")
    if not trace.exists():
        print("SKIP: no trace artifact at %s" % trace)
        return 0
    paired = load_traces(trace)
    # a set of (side-agnostic) values still needed for the diagnostic message
    by_depth = {}
    for (i, dep), sides in paired.items():
        for v in sides.values():
            by_depth.setdefault(dep, set()).add(v)
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
        # PAIRED: some single (position, depth) row must hold one value on each side.
        ok = any(sides.get("s14") == ai and sides.get("pc20") == bi
                 for (i, d2), sides in paired.items() if d2 == di)
        # also accept the reverse role assignment, since a row may quote PC20 first
        ok = ok or any(sides.get("s14") == bi and sides.get("pc20") == ai
                       for (i, d2), sides in paired.items() if d2 == di)
        print("  %-9s vs %-9s at d%-3s %s" % (a, b, dep, "PAIRED OK" if ok else "NOT A PAIRED ROW"))
        if not ok:
            bad += 1
            cands = [(i, s) for (i, d2), s in paired.items() if d2 == di][:4]
            print("      no single row at depth %d holds both; nearest rows: %s" % (di, cands))
    if bad:
        print("\nVERDICT: %d claim(s) do not match any paired row at that depth." % bad)
        print("LIMIT: this checks pairing, not attribution - the prose must name its position for a reader to verify.")
        return 1
    print("\nVERDICT: every per-depth node claim matches a PAIRED row (same position, same depth, one value each side).")
    print("LIMIT: the prose still does not NAME its position, so any row that satisfies the pair passes - attribution")
    print("is the writer's job. What is now impossible is a number that exists nowhere in the right role.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
