#!/usr/bin/env python3
"""Print the step table from the raw result files in this folder."""
from pathlib import Path

here = Path(__file__).resolve().parent

def grab(path, needle, which=0):
    text = (here / path).read_text(encoding="utf-8", errors="replace")
    found = [line.strip() for line in text.splitlines() if needle in line]
    if which < len(found):
        return found[which]
    return "MISSING"

def field(path, key):
    for line in (here / path).read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(key + " "):
            return line.split(None, 1)[1]
    return "MISSING"

rows = [
    ("STEP 1 seat", "done", "SEAT.txt", (here / "SEAT.txt").read_text(encoding="utf-8").strip()),
    ("STEP 2 honesty B", "done", "HONESTY_B.txt", grab("HONESTY_B.txt", "bench depth 11")),
    ("STEP 2 O depth 12", "done", "sums.txt", grab("sums.txt", "sum ", 0)),
    ("STEP 2 G depth 12", "done", "sums.txt", grab("sums.txt", "sum ", 1)),
    ("proof off O", "done", "compare_off_O.txt", "differ " + field("compare_off_O.txt", "differ")),
    ("proof off G", "done", "compare_off_G.txt", "differ " + field("compare_off_G.txt", "differ")),
    ("proof on O defaults", "done", "compare_on_O.txt", "differ " + field("compare_on_O.txt", "differ")),
    ("proof on spins 0", "done", "compare_on_zero_O.txt", "differ " + field("compare_on_zero_O.txt", "differ")),
    ("proof sanitizer clean", "done", "sanitizer_lines.txt", grab("sanitizer_lines.txt", "clean runtime_error")),
    ("proof sanitizer scratch", "done", "sanitizer_lines.txt", grab("sanitizer_lines.txt", "scratch_line")),
    ("proof asan symbols", "done", "asan_nm_count.txt", (here / "asan_nm_count.txt").read_text(encoding="utf-8").strip()),
    ("match 1106", "done", "match_result.txt", grab("match_result.txt", "Elo:")),
    ("partner apply", "done", "partner_apply_check.txt", grab("partner_apply_check.txt", "exit")),
    ("partner honesty", "done", "HONESTY_PARTNER.txt", grab("HONESTY_PARTNER.txt", "bench depth 11")),
    ("partner off O", "done", "partner_compare_off_O.txt", "differ " + field("partner_compare_off_O.txt", "differ")),
    ("partner on vs their rows", "done", "partner_compare_on_O.txt", "differ " + field("partner_compare_on_O.txt", "differ")),
    ("partner match 600", "done", "match_partner.log", grab("match_partner.log", "Elo:")),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
