#!/usr/bin/env python3
"""swarm seat 01, job 2 table: read asan/results.json + asan/results_fix.json and write the job's table.

Nothing here is typed by hand; every row comes from a committed raw file produced by a committed script.
"""
import json
import sys
from collections import Counter


def main(jobdir):
    rows = json.load(open(jobdir + "/pc/results.json"))
    fix = json.load(open(jobdir + "/pc/results_fix.json"))
    lines = []
    lines.append("job 2 table: extreme numbers in the FEN fields (ASan+UBSan build)")
    lines.append("")
    lines.append("case\tgroup\trefused\tengine_answer\tbestmove\tperft2_engine\tpy_perft2\tmatch")
    refused = 0
    crashes = 0
    san = 0
    for r in rows:
        refusal = r["refusal"][0] if r["refusal"] else "(accepted)"
        ans = refusal
        if r.get("crashed"):
            crashes += 1
        if r["sanitizer"]:
            san += len(r["sanitizer"])
        if r["refused"]:
            refused += 1
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
            r["case"], r["group"], r["refused"], ans, r["bestmove"],
            r["perft2_engine"], r["py_perft2"], r["perft_match"]))
    for r in fix:
        refusal = r["refusal"][0] if r["refusal"] else "(accepted)"
        if r["refused"]:
            refused += 1
        lines.append("%s\tcorrected\t%s\t%s\t-\t%s\t%s\t%s" % (
            r["case"], r["refused"], refusal, r["perft2_engine"], r["py_perft2"], r["match"]))
    total = len(rows) + len(fix)
    lines.append("")
    lines.append("cases: %d" % total)
    lines.append("refused: %d" % refused)
    lines.append("accepted: %d" % (total - refused))
    lines.append("crashes: %d" % crashes)
    lines.append("sanitizer lines: %d" % san)
    matched = sum(1 for r in rows if r["perft_match"]) + sum(1 for r in fix if r["match"])
    judged = sum(1 for r in rows if r["perft2_engine"] is not None and r["py_perft2"] is not None)
    judged += sum(1 for r in fix if r["perft2_engine"] is not None and r["py_perft2"] is not None)
    lines.append("perft 2 equal to python-chess: %d of %d judged" % (matched, judged))
    groups = Counter(r["group"] for r in rows)
    lines.append("")
    lines.append("by group: " + ", ".join("%s=%d" % (k, v) for k, v in sorted(groups.items())))
    # which halfmove values were accepted
    hm_acc = []
    for r in rows:
        if r["group"] == "halfmove" and not r["refused"]:
            hm_acc.append(r["case"].split("_")[1])
    lines.append("halfmove values ACCEPTED: " + ", ".join(hm_acc))
    text = "\n".join(lines) + "\n"
    open(jobdir + "/pc/table.txt", "w").write(text)
    print(text)


if __name__ == "__main__":
    main(sys.argv[1])
