#!/usr/bin/env python3
"""Print report numbers from raw files. The last Elo and Games lines are the final ones."""
from pathlib import Path

root = Path(__file__).resolve().parent

def text(name):
    return (root / name).read_text(encoding="utf-8")

def last(name, needle):
    found = None
    for line in text(name).splitlines():
        if needle in line:
            found = line
    if found is None:
        raise SystemExit("missing " + needle + " in " + name)
    return found

def first(name, needle):
    for line in text(name).splitlines():
        if needle in line:
            return line
    raise SystemExit("missing " + needle + " in " + name)

print("step | status | evidence | result")
rows = [
    ("1 seat", "done", "SEAT.txt stamps.txt", first("SEAT.txt", "seat ")),
    ("2 honesty B and baseline sums", "done", "HONESTY_B.txt B_O_d12.sum B_G_d12.sum",
     first("HONESTY_B.txt", "bench11=") + " ; " + first("B_O_d12.sum", "sum=") + " ; " + first("B_G_d12.sum", "sum=")),
    ("3 patch applies, off identical, on differs", "done", "apply_check.txt compare_B_Poff_O.txt compare_B_Poff_G.txt compare_B_Pon_O.txt",
     text("apply_check.txt").strip() + " ; " + first("compare_B_Poff_O.txt", "node_differ=") + " ; " + first("compare_B_Poff_G.txt", "node_differ=") + " ; " + first("compare_B_Pon_O.txt", "node_differ=")),
    ("3 uci options", "done", "uci_options_idea.txt", text("uci_options_idea.txt").strip().replace("\n", " ; ")),
    ("3 sanitizer", "done", "asan_nm_count.txt asan_g100.san asan_bug.san",
     "nm=" + text("asan_nm_count.txt").strip() + " ; " + first("asan_g100.san", "sanitizer_lines=") + " ; " + first("asan_bug.san", "sanitizer_lines=")),
    ("3 match", "done", "match_s34.log", last("match_s34.log", "Elo:") + " ; " + last("match_s34.log", "Games:")),
    ("4 partner", "done", "partner_apply.txt partner_compare.txt partner_honesty.txt partner_match.log",
     text("partner_apply.txt").strip() + " ; " + first("partner_compare.txt", "on_vs_partner_file") + " ; " + last("partner_match.log", "Games:")),
    ("5 report", "done", "REPORT.md RESULT.txt", "this file"),
]
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
print("--- final match ---")
print(last("match_s34.log", "Elo:"))
print(last("match_s34.log", "Games:"))
print("--- final partner match ---")
print(last("partner_match.log", "Elo:"))
print(last("partner_match.log", "Games:"))
print("--- on sum ---")
print(text("P_on_O_d12.sum").rstrip())
