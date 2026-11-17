#!/usr/bin/env python3
"""analyse2.py RESULTS OUT

Tables for job7, generated from the raw per-FEN table only. Also classifies the refusal
REASONS, which job1 did not do (its table kept the answer line but never summarised it)."""
import re
import sys
from collections import Counter

REASON = re.compile(r"invalid FEN: ([a-z\- ]+)")


def main():
    path, out = sys.argv[1], sys.argv[2]
    rows = []
    for ln in open(path):
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 9:
            rows.append(p)
    verdict = Counter(r[6] for r in rows)
    kind = Counter(r[2] for r in rows)
    acc = [r for r in rows if r[6] == "ACCEPTED"]
    acc_inv = [r for r in acc if r[5] != "1"]
    lines = ["| measure | count |", "|---|---|"]
    for k in ("REFUSED", "ACCEPTED"):
        lines.append("| %s | %d |" % (k, verdict.get(k, 0)))
    lines.append("| accepted & python-chess valid | %d |" % sum(1 for r in acc if r[5] == "1"))
    lines.append("| accepted & python-chess INVALID | %d |" % len(acc_inv))
    lines.append("| python-invalid share of accepted | %.2f %% |" % (100.0 * len(acc_inv) / max(len(acc), 1)))
    lines.append("")
    lines.append("| mutation kind | drawn | accepted | refused | acceptance rate |")
    lines.append("|---|---|---|---|---|")
    for k in sorted(kind):
        a = sum(1 for r in rows if r[2] == k and r[6] == "ACCEPTED")
        t = kind[k]
        lines.append("| %s | %d | %d | %d | %.1f %% |" % (k, t, a, t - a, 100.0 * a / t))
    lines.append("")
    lines.append("| accepted-but-python-invalid FEN | engine bestmove |")
    lines.append("|---|---|")
    for r in acc_inv:
        lines.append("| `%s` | %s |" % (r[4], r[7]))
    text = "\n".join(lines)
    open(out, "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()