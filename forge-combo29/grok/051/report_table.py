#!/usr/bin/env python3
"""Step table. Status words are fixed; numbers are read from the raw files."""
from pathlib import Path

seat = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (seat / name).read_text().strip().replace("\n", " | ")


rows = [
    ("1 seat", "done", "SEAT.txt stamps.txt", "seat 051 idea 1"),
    ("2 honesty B", "done", "HONESTY_B.txt", text("HONESTY_B.txt")),
    ("2 O and G on B", "done", "B_O.sum B_G.sum", text("B_O.sum") + " || " + text("B_G.sum")),
    ("3a read", "done", "include/forge/search.hpp", "EXISTS include/forge/search.hpp:351"),
    ("3b prediction", "done", "prediction.txt", "locked before measuring P"),
    ("3c patch", "done", "idea.patch.txt apply_check.txt", text("apply_check.txt")),
    ("3d honesty P", "done", "honesty_p_summary.txt", text("honesty_p_summary.txt")),
    ("3d off", "done", "compare_off_O.txt compare_off_G.txt", text("compare_off_O.txt") + " || " + text("compare_off_G.txt")),
    ("3d on", "done", "compare_on_O.txt", text("compare_on_O.txt")),
    ("3d uci", "done", "uci_options.txt", text("uci_options.txt")),
    ("3d sanitizer", "done", "asan_G100_sanitizer.txt asan_G100.meta asan_scratch_sanitizer.txt", text("asan_G100_sanitizer.txt") + " || " + text("asan_scratch_sanitizer.txt")),
    ("3e match", "done", "match_result.txt match_og/games.pgn", text("match_result.txt")),
    ("4 partner", "done", "partner_cmp_off_O.txt partner_cmp_on_O.txt partner_result.txt", text("partner_cmp_off_O.txt") + " || " + text("partner_cmp_on_O.txt") + " || " + text("partner_result.txt")),
]
print("step | status | evidence | result")
for row in rows:
    print(" | ".join(row))
