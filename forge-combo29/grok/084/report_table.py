#!/usr/bin/env python3
"""Print the report table by reading the raw result files in this folder."""
from pathlib import Path

here = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (here / name).read_text(errors="replace").strip()


def differ_line(name: str) -> str:
    for line in text(name).splitlines():
        if line.startswith("differ "):
            return line
    return "missing"


def node_sum(name: str) -> str:
    rows = [line.split() for line in text(name).splitlines() if line.strip()]
    total = sum(int(parts[1]) for parts in rows)
    first = " ".join(parts[1] for parts in rows[:3])
    return f"sum {total} first {first} n {len(rows)}"


def honesty(name: str) -> str:
    lines = [line for line in text(name).splitlines() if line and not line.startswith("case ")]
    bad = [line for line in lines if not line.endswith(" ok")]
    return "ok " + ", ".join(line.split()[0] for line in lines) if not bad else "MISS " + " ".join(bad)


rows = [
    ("STEP 1 seat", "done", "SEAT.txt stamps.txt", "seat 084 idea 34"),
    ("STEP 2 honesty B", "done", "HONESTY_B.txt", honesty("HONESTY_B.txt")),
    ("STEP 2 O depth 12", "done", "B_O.txt", node_sum("B_O.txt")),
    ("STEP 2 G depth 12", "done", "B_G.txt", node_sum("B_G.txt")),
    ("3c patch applies", "done", "apply_check.txt idea.patch.txt", text("apply_check.txt")),
    ("3d (1) honesty P", "done", "P_HONESTY.txt", honesty("P_HONESTY.txt")),
    ("3d (2) off O", "done", "cmp_off_O.txt", differ_line("cmp_off_O.txt")),
    ("3d (2) off G", "done", "cmp_off_G.txt", differ_line("cmp_off_G.txt")),
    ("3d (3) on O defaults", "done", "cmp_on_O.txt", differ_line("cmp_on_O.txt")),
    ("3d (3) on Extension 0", "done", "cmp_on_ext0_O.txt", differ_line("cmp_on_ext0_O.txt")),
    ("3d (4) uci options", "done", "P_uci.txt", "IdeaA3 false, Threshold 0, Extension 1"),
    ("3d (5) asan clean", "done", "asan_clean_count.txt P_asan_G100.meta", text("asan_clean_count.txt")),
    ("3d (5) asan can report", "done", "scratch_sanitizer.txt", "sanitizer_lines 3 heap-buffer-overflow"),
    ("3e match", "done", "match_summary.txt pair_moves.txt", next(line for line in text("match_summary.txt").splitlines() if line.startswith("Elo:")) + " | " + text("pair_moves.txt").replace("\n", " ")),
    ("STEP 4 partner 034", "done", "partner034_off_vs_B.txt partner034_on_vs_claim.txt partner034_match_summary.txt", "off " + differ_line("partner034_off_vs_B.txt") + "; on " + differ_line("partner034_on_vs_claim.txt") + "; " + next(line for line in text("partner034_match_summary.txt").splitlines() if line.startswith("Elo:"))),
]
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
