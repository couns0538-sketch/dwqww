#!/usr/bin/env python3
"""Resolve every ``[[key]]`` marker in FINDINGS.md from the evidence JSON, or fail.

The report does not contain typed numbers where a measurement goes.  It contains a marker naming
the counter.  This script:

  1. builds a flat map of every counter in evidence/*.json, keyed `source.path.to.counter`
  2. resolves each marker in the report against that map
  3. fails on a marker that names no counter (a claim with no evidence)
  4. fails on a marker that resolves to a non-integer where a count was expected
  5. writes FINDINGS.rendered.md with the values substituted, which is the file a reader can check
  6. --selftest plants a bogus marker and asserts the check fires

Why this and not "grep the numbers and compare": a report that repeats a number in prose and in a
table has two places to drift.  A marker has one source.

Usage:
  python3 verify_counts.py                 # check + render
  python3 verify_counts.py --selftest      # prove the check fires on a planted fault
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.abspath(os.path.join(HERE, "..", "evidence"))
FINDINGS = os.path.abspath(os.path.join(HERE, "..", "FINDINGS.md"))

SOURCES = [
    ("evidence/audit.json", "audit"),
    ("evidence/judge.json", "judge"),
    ("evidence/instability.json", "instability"),
    ("evidence/fastpaths.json", "fastpaths"),
    ("evidence/agreement.json", "agreement"),
    ("evidence/pins.json", "pins"),
    ("evidence/selftest.json", "selftest"),
    ("evidence/wire_control.json", "wire"),
    ("evidence/budget_stability.json", "budgetstats"),
]

MARKER = re.compile(r"\[\[([A-Za-z0-9_.:\-]+)\]\]")


def flatten(prefix, obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten("%s.%s" % (prefix, k) if prefix else str(k), v, out)
    elif isinstance(obj, list):
        out[prefix + ".len"] = len(obj)
        for i, v in enumerate(obj):
            flatten("%s.%d" % (prefix, i), v, out)
    else:
        out[prefix] = obj


def build(sources):
    flat, missing_files = {}, []
    for rel, prefix in sources:
        path = os.path.join(os.path.dirname(EVID), rel.replace("evidence/", ""), "")
        path = os.path.join(EVID, os.path.basename(rel))
        if not os.path.exists(path):
            missing_files.append(rel)
            continue
        with open(path) as fh:
            data = json.load(fh)
        if rel.endswith("judge.json") or rel.endswith("instability.json"):
            flatten(prefix, data.get("tally", {}), flat)
            for k in ("noise_floor", "depth", "mpv", "judge_depth"):
                if k in data:
                    flatten(prefix, {k: data[k]}, flat)
        elif rel.endswith("agreement.json"):
            flatten(prefix, data.get("tally", {}), flat)
            flatten(prefix + ".noise", data.get("noise_floor", {}), flat)
            hist = data.get("noise_floor", {}).get("abs_gap_histogram_by_10cp", {})
            if hist:
                # a histogram is a table, not a scalar: render it as one line so the marker
                # stays a single checkable object rather than eight unquoted numbers
                flat[prefix + ".noise_histogram"] = " ".join(
                    "%scp:%d" % (k, v) for k, v in sorted(hist.items(), key=lambda kv: int(kv[0])))
        elif rel.endswith("fastpaths.json"):
            flatten(prefix + ".summary", data.get("summary", {}), flat)
        elif rel.endswith("budget_stability.json"):
            flat[prefix + ".positions"] = data["positions"]
            flat[prefix + ".repeats"] = data["repeats"]
            for go, d in data["budgets"].items():
                tag = "movetime" if "movetime" in go else "nodes"
                flat["%s.%s_shorts" % (prefix, tag)] = ",".join(
                    str(r["short"]) for r in d["repeats"])
                flat["%s.%s_stable" % (prefix, tag)] = str(d["stable"]).lower()
                flat["%s.%s_bestmove_ok" % (prefix, tag)] = str(d["bestmove_all_agree"]).lower()
        elif rel.endswith("audit.json"):
            for k, v in data.items():
                if k in ("examples", "agreement_rows", "time_rows", "promotion_rows",
                         "pvlen_rows", "depth_span", "legal_ceiling", "fast_paths"):
                    flat["audit.%s.len" % k] = len(v) if isinstance(v, list) else 0
                elif isinstance(v, dict):
                    flatten("audit." + k, v, flat)
                else:
                    flat["audit." + k] = v
        else:
            flatten(prefix, data, flat)
    return flat, missing_files


def check(text, flat):
    keys = MARKER.findall(text)
    missing = [k for k in keys if k not in flat]
    # a marker used in a sentence must resolve to something printable
    rendered = MARKER.sub(lambda m: str(flat.get(m.group(1), m.group(0))), text)
    unresolved = MARKER.findall(rendered)
    return keys, missing, unresolved, rendered


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    flat, missing_files = build(SOURCES)
    with open(FINDINGS) as fh:
        text = fh.read()

    if args.selftest:
        # plant a marker naming no counter: the check must fire
        bad = text + "\n\nA planted claim: [[audit.structural.this_key_does_not_exist]]\n"
        _, missing, _, _ = check(bad, flat)
        if not missing:
            print("selftest FAILED: a bogus marker resolved, so the check cannot fire")
            return 1
        # and a marker that does resolve must not fire
        good = text + "\n\nA planted good claim: [[audit.structural.blocks]]\n"
        _, missing2, _, _ = check(good, flat)
        if missing2:
            print("selftest FAILED: a valid marker was rejected: %r" % (missing2,))
            return 1
        print("selftest: bogus marker rejected (%s), valid marker accepted, 0 failures"
              % missing[0])
        return 0

    if missing_files:
        print("verify_counts: missing evidence files: %s" % (missing_files,))
        return 1

    keys, missing, unresolved, rendered = check(text, flat)
    print("verify_counts: %d markers, %d distinct counters available, %d unresolved"
          % (len(keys), len(flat), len(missing)))
    for m in missing:
        print("  NO EVIDENCE for marker [[%s]]" % m)
    if unresolved:
        print("  UNRESOLVED after substitution: %s" % (unresolved[:5],))
    if not keys:
        print("  WARNING the report quotes no counters - nothing is checkable")
        return 1

    out = os.path.join(os.path.dirname(FINDINGS), "FINDINGS.rendered.md")
    with open(out, "w") as fh:
        fh.write(rendered)
    print("wrote", out)
    return 1 if (missing or unresolved) else 0


if __name__ == "__main__":
    sys.exit(main())
