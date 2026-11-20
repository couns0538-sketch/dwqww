#!/usr/bin/env python3
"""Print the measured facts the report quotes. Reads only files in this folder."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
NAMES = [
    "prediction.txt",
    "proof_B_O_sum.txt",
    "proof_B_G_sum.txt",
    "proof_off_O.txt",
    "proof_off_G.txt",
    "proof_on_O.txt",
    "proof_on_O_sum.txt",
    "match_summary.txt",
    "asan_G100_finding.txt",
    "asan_scratch_finding.txt",
    "apply_check.txt",
    "partner_proof_off.txt",
    "partner_proof_on.txt",
    "partner_off_sum.txt",
    "partner_on_sum.txt",
    "partner_on_O.sum",
    "partner_match.parse",
    "partner_match_summary.txt",
    "partner_commit.txt",
]


def main():
    meta = (ROOT / "asan_G100_d10.meta").read_text(encoding="utf-8")
    for line in meta.splitlines():
        if "__asan_" in line:
            print(line)
    for name in NAMES:
        print("===== " + name + " =====")
        print((ROOT / name).read_text(encoding="utf-8").rstrip("\n"))


if __name__ == "__main__":
    main()
