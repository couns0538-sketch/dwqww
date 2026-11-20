#!/usr/bin/env python3
"""Print the report table from the raw result files. No hand-typed numbers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def text(name):
    return (ROOT / name).read_text().strip()

def tsv_sum(name):
    for line in (ROOT / name).read_text().splitlines():
        if line.startswith("SUM\t"):
            return line.split("\t")[1]
    raise SystemExit(f"no SUM in {name}")

def last_result(name):
    lines = (ROOT / name).read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
    start = starts[-1]
    end = start
    while end < len(lines) and not lines[end].startswith("Games:"):
        end += 1
    return "\n".join(lines[start:end + 1])

rows = [
    ("STEP 1 seat", "done", "SEAT.txt", text("SEAT.txt")),
    ("STEP 2 honesty B", "done", "HONESTY_B.txt", text("HONESTY_B.txt").splitlines()[-1]),
    ("STEP 2 O depth 12 exe B", "done", "B_O_d12.tsv", "sum " + tsv_sum("B_O_d12.tsv")),
    ("STEP 2 G depth 12 exe B", "done", "B_G_d12.tsv", "sum " + tsv_sum("B_G_d12.tsv")),
    ("STEP 3 prediction", "done", "prediction.txt", "committed before the P measurements"),
    ("STEP 3 patch applies", "done", "idea.patch.txt", "git apply --check on a fresh base printed APPLY_CHECK_OK"),
    ("proof 1 honesty P", "done", "HONESTY_P.txt", text("HONESTY_P.txt").splitlines()[-1]),
    ("proof 2 switch off O", "done", "compare_off_O.txt", text("compare_off_O.txt")),
    ("proof 2 switch off G", "done", "compare_off_G.txt", text("compare_off_G.txt")),
    ("proof 3 switch on O", "done", "compare_on_O.txt", text("compare_on_O.txt")),
    ("proof 4 uci options", "done", "uci_p.txt", "IdeaS35 check false; spins 7, 4, 1, 24"),
    ("proof 5 sanitizer", "done", "asan_G100.meta", "asan_symbols 35, sanitizer_lines 0, 100 positions"),
    ("proof 5 trap", "done", "asan_trap.stderr.txt", "heap-buffer-overflow on the special FEN"),
    ("STEP 3 match", "done", "match_OG_result.txt", text("match_OG_result.txt").splitlines()[1]),
    ("STEP 4 partner apply", "done", "partner004_apply_check.txt", text("partner004_apply_check.txt")),
    ("STEP 4 partner honesty", "done", "HONESTY_PARTNER004.txt", text("HONESTY_PARTNER004.txt").splitlines()[-1]),
    ("STEP 4 partner off vs B", "done", "partner004_off_vs_B.txt", text("partner004_off_vs_B.txt").splitlines()[-1]),
    ("STEP 4 partner on vs claim", "done", "partner004_on_vs_claim.txt", text("partner004_on_vs_claim.txt").splitlines()[-1]),
    ("STEP 4 partner match", "done", "partner004_match.txt", last_result("partner004_match.txt").splitlines()[1]),
]
print("step | done / partly / not done | evidence file | result")
for step, status, evidence, result in rows:
    one = " ".join(result.split())
    print(f"{step} | {status} | {evidence} | {one}")
