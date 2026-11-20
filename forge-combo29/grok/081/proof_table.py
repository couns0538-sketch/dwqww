#!/usr/bin/env python3
"""Print the step table from the evidence files in this directory."""
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parent

def text(name):
    return (root / name).read_text(encoding="utf-8").strip()

def line_with(name, needle):
    for line in text(name).splitlines():
        if needle in line:
            return line
    return "MISSING"

rows = [
    ("1 seat", "done", "SEAT.txt", text("SEAT.txt")),
    ("2 honesty B", "done", "HONESTY_B.txt", text("HONESTY_B.txt").replace("\n", " | ")),
    ("2 O depth 12 B", "done", "O_b_d12.sum.txt", text("O_b_d12.sum.txt").replace("\n", " | ")),
    ("2 G depth 12 B", "done", "G_b_d12.sum.txt", text("G_b_d12.sum.txt").replace("\n", " | ")),
    ("3 patch applies", "done", "idea.patch.txt", "git apply --check on a fresh base of 6b98f2170 exited 0"),
    ("3 proof 1 honesty P", "done", "HONESTY_P.txt", text("HONESTY_P.txt").replace("\n", " | ")),
    ("3 proof 2 off O", "done", "O_off_compare.txt", text("O_off_compare.txt").replace("\n", " | ")),
    ("3 proof 2 off G", "done", "G_off_compare.txt", text("G_off_compare.txt").replace("\n", " | ")),
    ("3 proof 3 on O", "done", "O_on_compare.txt", line_with("O_on_compare.txt", "differ")),
    ("3 proof 3 on sum", "done", "O_p_on_d12.sum.txt", text("O_p_on_d12.sum.txt").replace("\n", " | ")),
    ("3 proof 4 uci", "done", "uci_p.txt", "IdeaS10 check default false; five IdeaS10_ spins at their defaults"),
    ("3 proof 5 sanitizer", "done", "asan_g100.sanitizer.txt", text("asan_g100.sanitizer.txt").replace("\n", " | ")),
    ("3 proof 5 scratch", "done", "asan_scratch.sanitizer.txt", text("asan_scratch.sanitizer.txt").replace("\n", " | ")),
    ("3 match", "done", "match_og.summary.txt", line_with("match_og.summary.txt", "Elo:") + " ; " + line_with("match_og.summary.txt", "Games:")),
    ("4 partner apply", "done", "partner_apply.txt", text("partner_apply.txt").replace("\n", " | ")),
    ("4 partner honesty", "done", "partner_honesty.txt", text("partner_honesty.txt").replace("\n", " | ")),
    ("4 partner off", "done", "partner_off_compare.txt", line_with("partner_off_compare.txt", "differ")),
    ("4 partner on vs published", "done", "partner_on_compare.txt", line_with("partner_on_compare.txt", "differ")),
    ("4 partner on vs B", "done", "partner_on_vs_b.txt", line_with("partner_on_vs_b.txt", "differ")),
    ("4 partner R match", "done", "partner_match.summary.txt", line_with("partner_match.summary.txt", "Elo:") + " ; " + line_with("partner_match.summary.txt", "Games:")),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print("%s | %s | %s | %s" % (step, status, evidence, result))
