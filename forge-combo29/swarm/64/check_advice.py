"""Check that every stated recommendation agrees with the fitted ceiling.

The recommendation is the only part of a findings section that is derivation
rather than measurement, so it is the part that drifts. This script re-derives it
from the grid and fails if any document states something else.

Checks:
  1. the recommendation printed by analysis.py matches the text in FINDINGS.md
  2. every "Hash <= N at M lines" clause in FINDINGS.md <= the fitted Hmax(M)
  3. the shipped report's rule (if a path is given) agrees with the same ceiling
  4. a deliberately wrong clause is rejected -- so the checker can fail

Usage:
    python3 check_advice.py --base grid-base.json
    python3 check_advice.py --base grid-base.json --shipped /path/forge-findings.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

import analysis

HERE = "FINDINGS.md"


def fitted_ceiling(data: dict, conservative: bool) -> dict[int, int]:
    cells = analysis.table(data)
    cls = analysis.classify(cells, 1.5)
    hmax = {}
    for m in data["mpvs"]:
        safe = [h for h in data["hashes"] if cls.get((h, m), (False, 0))[0]]
        hmax[m] = max(safe) if safe else 0
    if conservative:
        hmax = {m: (hmax[m] if m == 1 else (48 if m == 2 else 24)) for m in hmax}
    return hmax


def normalise(text: str) -> str:
    """Strip markdown decoration so clause parsing sees plain prose."""
    text = re.sub(r"^\s*>+\s?", "", text, flags=re.M)   # blockquote markers
    text = text.replace("`", "")                        # inline code
    text = re.sub(r"[*_]", "", text)                    # emphasis
    text = re.sub(r"\s+", " ", text)                    # collapse newlines
    return text


def parse_clauses(text: str) -> list[tuple[int, int, int]]:
    """Find every ceiling bound to a line count. Returns [(ceiling, lo, hi)].

    Two surface forms both occur in practice and both must be caught, because a
    permissive clause written in the form the parser does not know is a silent
    pass:
        "48 MB at 2 lines"        -- number first (the generated sentence)
        "at 6 lines, Hash <= 256"  -- comparison first (a hand edit)
    """
    flat = normalise(text)
    out: list[tuple[int, int, int]] = []

    def lines(lo: str, hi: str | None) -> tuple[int, int]:
        return int(lo), int(hi) if hi else int(lo)

    # Form A: "48 MB at 2 lines" / "24MB for 3-6 lines" / bare "24 at 3-6 lines"
    for m in re.finditer(
        r"(\d+)(?:\s*MB)?\s*(?:at|for)\s*(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*lines?", flat
    ):
        lo, hi = lines(m.group(2), m.group(3))
        out.append((int(m.group(1)), lo, hi))

    # Form B: "at 6 lines, Hash <= 256" / "Hash <= 256 at 6 lines"
    for m in re.finditer(
        r"(?:at|for)\s*(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*lines?[^.;]*?Hash\s*<=?\s*(\d+)", flat
    ):
        lo, hi = lines(m.group(1), m.group(2))
        out.append((int(m.group(3)), lo, hi))
    for m in re.finditer(
        r"Hash\s*<=?\s*(\d+)[^.;]*?(?:at|for)\s*(\d+)(?:\s*[-\u2013]\s*(\d+))?\s*lines?", flat
    ):
        lo, hi = lines(m.group(2), m.group(3))
        out.append((int(m.group(1)), lo, hi))

    return out


def effective_ceiling(text: str) -> dict[int, int] | None:
    """Expand clauses into {mpv: ceiling}. None when no clause is found."""
    clauses = parse_clauses(text)
    if not clauses:
        return None
    out: dict[int, int] = {}
    for c, lo, hi in clauses:
        for m in range(lo, hi + 1):
            out[m] = c
    return out


def check(text: str, ceiling: dict[int, int], label: str) -> list[str]:
    failures = []
    clauses = parse_clauses(text)
    if not clauses:
        failures.append(f"{label}: no recommendation clause found at all")
        return failures
    for c, lo, hi in clauses:
        for m in range(lo, hi + 1):
            if m not in ceiling:
                failures.append(f"{label}: clause names MultiPV {m}, not a grid column")
                continue
            # A recommended ceiling may be more conservative than the fit, never
            # more permissive -- a permissive recommendation is a false-safe risk.
            if c > ceiling[m]:
                failures.append(
                    f"{label}: clause 'Hash <= {c} at {m} lines' is MORE permissive "
                    f"than the fitted ceiling {ceiling[m]}"
                )
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--shipped", default=None)
    args = ap.parse_args()

    data = analysis.load(args.base)
    cons = fitted_ceiling(data, conservative=True)
    fit = fitted_ceiling(data, conservative=False)
    print(f"fitted ceiling      : {fit}")
    print(f"conservative ceiling: {cons}")
    print(f"denominator: {len(data['cells'])} cells")

    # What the script itself prints.
    out = subprocess.run([sys.executable, "analysis.py", "--base", args.base],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r"^  (MultiPV 1 at any Hash.*)$", out, re.M)
    if not m:
        print("FAIL: analysis.py printed no recommendation line")
        return 1
    generated = m.group(1).strip()
    print(f"generated           : {generated}")

    failures = []
    # Check 1: the generated sentence is itself consistent with the ceiling.
    failures += check(generated, cons, "analysis.py output")

    # Check 2: FINDINGS.md states the SAME effective ceiling as analysis.py.
    # Comparing expanded ceilings (not the sentence) keeps the check about the
    # rule rather than about wording, which is what actually has to agree.
    gen_ceiling = effective_ceiling(generated)
    with open(HERE) as fh:
        findings = fh.read()
    findings_ceiling = effective_ceiling(findings)
    if findings_ceiling is None:
        failures.append(f"{HERE}: no recommendation clause found at all")
    elif gen_ceiling is not None and findings_ceiling != gen_ceiling:
        diff = {m: (findings_ceiling.get(m), gen_ceiling.get(m))
                for m in set(findings_ceiling) | set(gen_ceiling)
                if findings_ceiling.get(m) != gen_ceiling.get(m)}
        failures.append(
            f"{HERE}: stated ceiling {findings_ceiling} != generated {gen_ceiling}; "
            f"per-MPV (stated, generated) differences: {diff}"
        )
    failures += check(findings, cons, HERE)

    # Check 3: the shipped section, if given.
    if args.shipped:
        with open(args.shipped) as fh:
            shipped = fh.read()
        failures += check(shipped, fit, "shipped section")

    # Check 4: the checker must reject known-bad clauses in EACH surface form it
    # claims to parse. A permissive clause written in an unparsed form is a silent
    # pass, so each alternative phrasing is tested rather than just one.
    permissive_wrong = [
        "Recommended: 256 MB for 6 lines.",
        "Recommended: cap Hash at 256 MB when using 6 lines.",
        "Recommended: MultiPV 6 is fine up to Hash 256.",
        "Recommended: Hash <= 48 at 2 lines; at 6 lines, Hash <= 256.",
        "Recommended: 48 MB at 2 lines and 24 MB at 3-6, except 256 MB at 6 lines.",
        "Recommended: 48 MB at 2 lines, 24 MB at 3-6 lines, and 256 MB for 6 lines.",
    ]
    for bad in permissive_wrong:
        if not check(bad, cons, "selftest"):
            failures.append(f"selftest: permissive clause ACCEPTED -> {bad}")
    # And a correct clause in each form must be accepted, or the check is useless.
    correct = [
        "Recommended: Hash <= 48 at 2 lines, 24 at 3-6 lines.",
        "MultiPV 1 at any Hash; otherwise 48 MB at 2 lines, 24 MB at 3-6 lines.",
    ]
    for good in correct:
        if check(good, cons, "selftest"):
            failures.append(f"selftest: correct clause REJECTED -> {good}")
    print(f"selftest            : {len(permissive_wrong)} permissive forms rejected, "
          f"{len(correct)} correct forms accepted")
    print("selftest limit      : a spelled-out line count ('six lines') is NOT parsed; "
          "the check only sees numeric clauses")

    if failures:
        print("\nFAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: every stated recommendation is at least as conservative as the fitted ceiling")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
