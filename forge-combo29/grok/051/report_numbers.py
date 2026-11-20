#!/usr/bin/env python3
"""Print the numbers the report cites, read from the raw files."""
from pathlib import Path

seat = Path(__file__).resolve().parent


def show(name: str) -> None:
    path = seat / name
    print(f"--- {name} ---")
    if not path.exists():
        print("MISSING")
        return
    text = path.read_text().rstrip()
    print(text if text else "(empty)")


for name in [
    "HONESTY_B.txt",
    "honesty_p_summary.txt",
    "partner_h_summary.txt",
    "B_O.sum",
    "B_G.sum",
    "P_off_O.sum",
    "P_off_G.sum",
    "P_on_O.sum",
    "compare_off_O.txt",
    "compare_off_G.txt",
    "compare_on_O.txt",
    "uci_options.txt",
    "asan_G100_sanitizer.txt",
    "asan_scratch_sanitizer.txt",
    "partner_off_O.sum",
    "partner_on_O.sum",
    "partner_cmp_off_O.txt",
    "partner_cmp_on_O.txt",
    "match_result.txt",
    "partner_result.txt",
    "prediction.txt",
]:
    show(name)
