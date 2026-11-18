#!/usr/bin/env python3
"""Compare the Job 4 UCI rows with Job 3 and verify reset controls."""
import argparse
import json
from pathlib import Path

IDENTITY = ("game", "ply", "fen", "nodes", "bestmove", "cnt")


def read_rows(path):
    with path.open(encoding="utf-8") as rows:
        for line in rows:
            yield json.loads(line)


def compare(new, reference, max_examples=1):
    total = different = 0
    for total, (new_row, reference_row) in enumerate(zip(read_rows(new), read_rows(reference), strict=True), 1):
        changes = [field for field in IDENTITY if new_row[field] != reference_row[field]]
        if changes:
            different += 1
            if different <= max_examples:
                print(f"Difference {different} at search {total}: {', '.join(changes)}")
                print(json.dumps({"new": new_row, "reference": reference_row}, separators=(",", ":")))
    if total != 6000:
        raise SystemExit(f"{new.name} vs {reference.name}: expected 6000 rows, got {total}")
    print(f"{new.name} vs {reference.name}: {total-different}/{total} identical, {different} differences.")
    return different


def baselines(raw, previous):
    for arm, old_name in (("A2", "A-soft-warm"), ("B2", "B-hard-warm"),
                          ("C2", "C-soft-cold"), ("D2", "D-hard-cold")):
        if compare(raw / f"{arm}.jsonl", previous / f"{old_name}.jsonl"):
            raise SystemExit(f"Unchanged-path gate failed for {arm}.")


def controls(raw):
    compare(raw / "G.jsonl", raw / "A2.jsonl", max_examples=5)
    if compare(raw / "H.jsonl", raw / "C2.jsonl"):
        raise SystemExit("Full-reset gate failed for H.")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=("baselines", "controls"))
parser.add_argument("raw", type=Path)
parser.add_argument("--job3-raw", type=Path)
args = parser.parse_args()
if args.stage == "baselines":
    if args.job3_raw is None:
        parser.error("baselines need --job3-raw")
    baselines(args.raw, args.job3_raw)
else:
    controls(args.raw)
