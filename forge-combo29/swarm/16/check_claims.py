#!/usr/bin/env python3
"""check_claims.py — a WEAK, HONEST-ABOUT-ITS-LIMITS prompt for the six failure habits. Read the verdict below.

MEASURED LIMITATION (I ran this on my own 36 reports): it produced 210 candidate lines and on inspection the
large majority were FALSE POSITIVES. Habit 3 fired 29 times, mostly on the word "identical" inside prose that DOES
report its sample size in the same paragraph; habit 5 fired 23 times on the word "cost" in sentences that never
made a comparison at all. Prose ABOUT rigour reads exactly like prose that LACKS rigour to a regex.

So: use it as a prompt to re-read a line, never as a verdict, and expect to dismiss most of what it shows.
What actually mechanises well and is worth trusting:
    habit 2 (a report with a median figure and no max/p99 anywhere)   - 3 hits on 36 reports, all worth checking
    habit 1 (a bare "N worse, M better" with no magnitude on the line) - 1 hit, and it was a real spot to look
    habit 6 (a zero-result claim with no planted case in the report)  - 7 hits, roughly half real
What does NOT mechanise: habits 3, 4 and 5. A single-case-as-property error is a judgement about whether the
sample in the surrounding text supports the sentence, and a regex cannot see the surrounding text. The reliable
form of those three is a READER's question, not a script's: "how many?", "what is the model?", "what does positive
mean?" - which is exactly how the six are worded in FINAL.

Kept in the folder as a demonstration of that boundary rather than as a gate. The header of the file says so.

usage:  python3 check_claims.py REPORT.md [REPORT.md ...]
        python3 check_claims.py --all          # every REPORT_*.md in the current directory

Each of the six checks from FINAL's STANDING CAUTION is turned into something a script can look for. The script
does not judge your work; it lists places where a claim is stated more strongly than its evidence, so you can
either add the sample size or soften the wording.

WHAT EACH CHECK LOOKS FOR (and why it is only a prompt, not a verdict)
---------------------------------------------------------------------
1. COUNT WITHOUT MAGNITUDE  — comparisons reported as "N worse, M better" with no magnitude anywhere near them.
2. MEDIAN WITHOUT TAIL      — a "median" figure with no max/p99/percentile/range mentioned in the same report.
3. SINGLE PROBE AS PROPERTY — words like "always", "exactly", "restores", "never", "proves" in a sentence that
                              contains no N, no count, and no "positions"/"pairs"/"runs" figure.
4. CORRELATION, NO MODEL    — an "r = " or "correlation" with no mention of how the predictor was built.
5. UNSTATED SIGN            — the words "cost"/"delta"/"gap"/"difference" near a number with no sign convention
                              stated anywhere in the report ("positive means", "from the mover", "worse is").
6. UNPLANTED CHECK          — a claim that something was "0 differences", "0 illegal", "no errors", "0 reports",
                              "none found" with no nearby mention of a planted/control/positive-control case.

Exit code is 0 always: this is a checklist that surfaces candidates, not a gate. A flagged line is often fine.
"""
import glob
import re
import sys

HABITS = [
    ("1 count-without-magnitude",
     re.compile(r"\b\d+\s+(?:worse|better)\b", re.I),
     "no magnitude (cp/ms/count) on this line",
     re.compile(r"\bcp\b|\bms\b|[+-]\d+\s*(?:cp|ms)", re.I)),
    ("2 median-without-tail",
     re.compile(r"\bmedian\b", re.I),
     None,   # handled at report level, not line level
     None),
    ("3 single-probe-as-property",
     re.compile(r"\b(always|never|exactly|restores|proves|identical)\b", re.I),
     "no sample size on this line",
     re.compile(r"\b\d+\s*(?:of|/)\s*\d+|\bN\s*=|\b\d+\s+(?:positions|pairs|runs|moves|games)\b|\b\d+/\d+", re.I)),
    ("4 correlation-without-model",
     re.compile(r"\br\s*=\s*[-0-9.]|correlat", re.I),
     "no mention of how the predictor was built",
     re.compile(r"predict|MG|EG|phase|model|convention|sum", re.I)),
    ("5 unstated-sign",
     re.compile(r"\b(cost|delta|gap|difference)\b", re.I),
     "no sign convention stated in this report",
     re.compile(r"positive means|from the mover|worse is|positive =|sign convention", re.I)),
    ("6 unplanted-check",
     re.compile(r"\b(0\s+differences?|0\s+illegal|no errors?|0\s+reports?|none found|0\s+failures?)\b", re.I),
     "no planted/control case mentioned in this report",
     re.compile(r"plant|control|deliberately|scratch|fake|counterexample", re.I)),
]


def check_report(path):
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"\n=== {path}: cannot read ({exc})")
        return 0
    lines = text.splitlines()
    print(f"\n=== {path}  ({len(lines)} lines)")
    total = 0
    for name, trigger, per_line_reason, exempt in HABITS:
        hits = []
        if name.startswith("2 "):
            # report-level: a median figure with no tail statistic anywhere
            if trigger.search(text):
                if not re.search(r"\b(max|p99|p90|percentile|range|worst)\b", text, re.I):
                    hits.append(("(whole report)", "no max / p99 / range anywhere in the report"))
        else:
            for i, l in enumerate(lines, 1):
                if not trigger.search(l):
                    continue
                if per_line_reason and exempt is not None and exempt.search(l):
                    continue
                if name.startswith("4 ") or name.startswith("5 ") or name.startswith("6 "):
                    # these are report-level exemptions: skip the line if the report satisfies the condition
                    if exempt is not None and exempt.search(text):
                        continue
                hits.append((f"line {i}", l.strip()[:110]))
        if hits:
            print(f"  [{name}] {len(hits)} candidate(s)")
            for where, snippet in hits[:6]:
                print(f"     {where}: {snippet}")
            if len(hits) > 6:
                print(f"     ... and {len(hits) - 6} more")
            total += len(hits)
    if total == 0:
        print("  no candidates for any of the six habits")
    return total


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--all" in sys.argv or not args:
        args = sorted(glob.glob("REPORT_*.md")) + sorted(glob.glob("*/REPORT_*.md"))
    if not args:
        print("no reports found; pass file names or run in a folder containing REPORT_*.md")
        return
    grand = 0
    for p in args:
        grand += check_report(p)
    print(f"\n--- {len(args)} report(s), {grand} candidate line(s) to review.")
    print("A candidate is not an error. It is a sentence stated more strongly than its evidence; add the sample")
    print("size, the tail statistic, the sign convention or the planted control — or soften the wording.")


if __name__ == "__main__":
    main()
