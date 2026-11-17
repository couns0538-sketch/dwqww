#!/usr/bin/env python3
"""Render the mutant table for FINDINGS.md from the result JSONs.

Every count in the prose is derived here too, and check_consistency.py re-derives
them from the same files and fails on a mismatch. A prose count beside a computed
table is a stale claim waiting for its next regeneration.

Usage: report_table.py <manifest.json> <results_rel.json> <results_asan.json> <loud_rel.json>
"""
import json
import sys

MESSAGES = {
    "magic": "bad magic",
    "version": "unsupported version",
    "header_bytes": "header_bytes must be 192",
    "inputs": "inputs must be 768",
    "hidden": "hidden must be a multiple of 32",
    "king_buckets": "king_buckets must be 1..32",
    "output_buckets": "output_buckets must be 1..16",
    "flags": "unknown flag bits",
    "qa/qb": "quantisation must be qa 255 / qb 64",
    "eval_scale": "eval_scale must be 1..10000",
    "reserved": "reserved header bytes must be zero",
    "king_map": "king_bucket_map entry out of range",
    "output_map": "output_bucket_map entry out of range",
    "size": "file size N != expected M",
    "too_small": "file too small for a v3 header",
    "checksum": "checksum mismatch",
    "residual": "residual v3 networks are not supported",
}


def short_message(text):
    """Compress a loader message to its class, keeping the numbers."""
    if "bad magic" in text:
        return "bad magic (expected FORGENN3)"
    if "unsupported version" in text:
        return text.split(": ", 1)[-1]
    if "must be 192" in text:
        return "header_bytes must be 192"
    if "inputs must be" in text:
        return "inputs must be 768"
    if "hidden must be" in text:
        return text.split(": ", 1)[-1]
    if "king_buckets must be" in text:
        return text.split(": ", 1)[-1]
    if "output_buckets must be" in text:
        return text.split(": ", 1)[-1]
    if "unknown flag bits" in text:
        return "unknown flag bits"
    if "quantisation must be" in text:
        return "quantisation must be qa 255 / qb 64"
    if "eval_scale must be" in text:
        return "eval_scale must be 1..10000"
    if "reserved header bytes" in text:
        return "reserved header bytes must be zero"
    if "king_bucket_map entry" in text:
        return "king_bucket_map entry out of range"
    if "output_bucket_map entry" in text:
        return "output_bucket_map entry out of range"
    if "file too small" in text:
        return "file too small for a v3 header"
    if "file size" in text:
        return text.split(": ", 1)[-1]
    if "checksum mismatch" in text:
        return "checksum mismatch"
    if "residual" in text:
        return "residual v3 networks are not supported"
    return text[:60]


def main():
    manifest = json.load(open(sys.argv[1]))
    rel = {r["name"]: r for r in json.load(open(sys.argv[2]))["results"]}
    asan = {r["name"]: r for r in json.load(open(sys.argv[3]))["results"]}
    loud = {r["name"]: r for r in json.load(open(sys.argv[4]))}

    print("| mutant | class | field changed | verdict | loader message | engine | ASan+UBSan lines |")
    print("|---|---|---|---|---|---|---|")
    for case in manifest["cases"]:
        name = case["name"]
        r = rel[name]
        a = asan[name]
        l = loud[name]
        verdict = r["probe_rel"]["verdict"]
        if verdict == "accept":
            shown = "loaded"
        elif verdict == "refuse":
            shown = "**refused**"
        else:
            shown = verdict
        msg = short_message(r["probe_rel"]["detail"]) if verdict != "accept" else "—"
        eng = "refused (exit 2)" if l and not any("loaded v3" in x for x in l.get("load_reply", [])) else "loaded"
        san = len(a["probe_asan"]["sanitizer_lines"])
        agree = "yes" if (verdict == "accept") == (case["expect"] == "accept") else "**NO**"
        if agree != "yes":
            print("!! expectation miss: %s expected %s got %s" % (name, case["expect"], verdict), file=sys.stderr)
        print("| `%s` | %s | %s | %s | %s | %s | %d |"
              % (name, case["class"], case["field"], shown, msg, eng, san))

    print()
    classes = {}
    for case in manifest["cases"]:
        r = rel[case["name"]]
        cls = case["class"]
        classes.setdefault(cls, {"refuse": 0, "accept": 0})
        classes[cls][r["probe_rel"]["verdict"]] += 1
    print("### Counts by class")
    print()
    print("| class | mutants | refused | loaded |")
    print("|---|---|---|---|")
    for cls in ("control", "header", "bomb", "checksum", "adversarial", "truncation"):
        c = classes[cls]
        print("| %s | %d | %d | %d |" % (cls, c["refuse"] + c["accept"], c["refuse"], c["accept"]))
    total = sum(c["refuse"] + c["accept"] for c in classes.values())
    print("| **total** | **%d** | **%d** | **%d** |"
          % (total, sum(c["refuse"] for c in classes.values()),
             sum(c["accept"] for c in classes.values())))
    print()
    san_total = sum(len(a["probe_asan"]["sanitizer_lines"]) for a in asan.values())
    print("sanitizer_lines_total %d" % san_total)


if __name__ == "__main__":
    main()
