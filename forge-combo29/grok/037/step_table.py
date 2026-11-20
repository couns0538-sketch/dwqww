#!/usr/bin/env python3
"""One row per step, read from the files in this folder."""
from pathlib import Path


def text(path: Path) -> str:
    return path.read_text().strip().replace("\n", " | ")


def main() -> None:
    here = Path(__file__).resolve().parent
    rows = [
        ("1 seat", "done", "SEAT.txt", text(here / "SEAT.txt")),
        ("2 honesty B", "done", "HONESTY_B.txt", text(here / "HONESTY_B.txt")),
        ("2 O and G sums", "done", "B_O_d12.meta", " ".join(
            line for line in (here / "B_O_d12.meta").read_text().splitlines()
            if line.startswith("sum=") or line.startswith("first3="))),
        ("2 G sum", "done", "B_G_d12.meta", " ".join(
            line for line in (here / "B_G_d12.meta").read_text().splitlines()
            if line.startswith("sum="))),
        ("3 prediction", "done", "prediction.txt", " ".join(
            line for line in (here / "prediction.txt").read_text().splitlines()
            if "9500069" in line or line.startswith("Test match"))),
        ("3 patch applies", "done", "apply_check.txt", text(here / "apply_check.txt")),
        ("3 proof 1 honesty P", "done", "HONESTY_P.txt", text(here / "HONESTY_P.txt")),
        ("3 proof 2 off", "done", "compare_off_O.txt compare_off_G.txt",
         text(here / "compare_off_O.txt") + " || " + text(here / "compare_off_G.txt")),
        ("3 proof 3 on", "done", "compare_on_O.txt", text(here / "compare_on_O.txt")),
        ("3 proof 3 wiring", "done", "compare_on_zero_O.txt", text(here / "compare_on_zero_O.txt")),
        ("3 proof 4 uci", "done", "uci_options_table.txt", text(here / "uci_options_table.txt")),
        ("3 proof 5 sanitizer", "done", "asan_G100_d10.meta asan_scratch.meta",
         " ".join(line for line in (here / "asan_G100_d10.meta").read_text().splitlines()
                  if line.startswith("nm_asan_count=") or line.startswith("sanitizer_lines="))
         + " || " + " ".join(line for line in (here / "asan_scratch.meta").read_text().splitlines()
                             if "AddressSanitizer" in line or line.startswith("sanitizer_lines=") or line.startswith("nm_asan_count="))),
        ("3 match", "done", "match_elo.txt", text(here / "match_elo.txt")),
        ("4 partner", "done", "partner_compare_off.txt partner_compare_on.txt match_partner_elo.txt",
         text(here / "partner_compare_off.txt") + " || " + text(here / "partner_compare_on.txt")),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")


if __name__ == "__main__":
    main()
