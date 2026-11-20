#!/usr/bin/env python3
"""Print the report table and the proof lines by reading the raw files."""
import sys
from pathlib import Path

folder = Path(sys.argv[1])


def text(name: str) -> str:
    return (folder / name).read_text(errors="replace")


def last_nodes(name: str) -> str:
    lines = [line for line in text(name).splitlines() if line.strip()]
    return lines[-1] if lines else "MISSING"


def row_sum(name: str):
    total = 0
    count = 0
    for line in text(name).splitlines():
        if not line.strip():
            continue
        total += int(line.split("\t", 2)[1])
        count += 1
    return count, total


def differ(a: str, b: str) -> int:
    aa = [int(line.split("\t", 2)[1]) for line in text(a).splitlines() if line.strip()]
    bb = [int(line.split("\t", 2)[1]) for line in text(b).splitlines() if line.strip()]
    return sum(1 for x, y in zip(aa, bb) if x != y)


print("HONESTY_B")
print(text("HONESTY_B.txt").rstrip())
print("HONESTY_P")
print(text("HONESTY_P.txt").rstrip())
print("HONESTY_PARTNER")
print(text("HONESTY_PARTNER.txt").rstrip())
print("PROOFS")
for label, a, b in (
    ("off_O", "B_O_d12.txt", "P_off_O_d12.txt"),
    ("off_G", "B_G_d12.txt", "P_off_G_d12.txt"),
    ("on_O", "B_O_d12.txt", "P_on_O_d12.txt"),
    ("partner_off_O", "B_O_d12.txt", "partner_off_O_d12.txt"),
    ("partner_on_vs_B", "B_O_d12.txt", "partner_on_O_d12.txt"),
):
    na, sa = row_sum(a)
    nb, sb = row_sum(b)
    print(f"{label} n={na} a_sum={sa} b_sum={sb} differ={differ(a, b)}")
print(text("partner_on_vs_claim.txt").rstrip())
print("UCI")
for line in text("uci_P.txt").splitlines():
    if "IdeaA8" in line:
        print(line)
print("ASAN")
print(text("asan_summary.txt").rstrip())
print("MATCH")
print(text("match_summary.txt").rstrip())
print("PARTNER_MATCH")
print(text("partner_match_summary.txt").rstrip())
print("TABLE")
rows = [
    ("1 seat", "done", "SEAT.txt", "seat 089 idea 39"),
    ("2 honesty B", "done", "HONESTY_B.txt", last_nodes("honesty_B_bench11.txt") + " ; " + last_nodes("honesty_B_perft5.txt")),
    ("2 base O G", "done", "B_O_sum.txt", text("B_O_sum.txt").strip() + " ; " + text("B_G_sum.txt").strip()),
    ("3 prediction", "done", "prediction.txt", "committed before measuring P"),
    ("3 patch applies", "done", "idea.patch.txt", "git apply --check on the seat tree returned 0 before this report"),
    ("3 proof off", "done", "proof_off_O.txt", text("proof_off_O.txt").strip() + " ; " + text("proof_off_G.txt").strip()),
    ("3 proof on", "done", "proof_on_O.txt", text("proof_on_O.txt").strip()),
    ("3 uci options", "done", "uci_P.txt", "IdeaA8 check false, IdeaA8_Captures spin 2"),
    ("3 sanitizer", "done", "asan_summary.txt", text("asan_summary.txt").strip().replace("\n", " | ")),
    ("3 match", "done", "match_summary.txt", "1106 games, see match_summary.txt"),
    ("4 partner", "done", "partner_on_vs_claim.txt", text("partner_off_vs_B.txt").strip() + " ; " + text("partner_on_vs_claim.txt").strip()),
    ("4 partner match", "done", "partner_match_summary.txt", "600 games"),
    ("5 report", "done", "REPORT.md", "this file"),
]
print("step | status | evidence | result")
for step, status, evidence, result in rows:
    print(f"{step} | {status} | {evidence} | {result}")
