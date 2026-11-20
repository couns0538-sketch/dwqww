#!/usr/bin/env python3
"""Print the report table from the raw evidence files in this folder."""
from pathlib import Path


def text(name: str) -> str:
    return Path(name).read_text()


def line_with(name: str, prefix: str) -> str:
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line
    raise SystemExit(f"no {prefix!r} in {name}")


def main() -> None:
    here = Path(__file__).resolve().parent
    rows = [
        ("1 seat", "done", "SEAT.txt", text("SEAT.txt").strip()),
        ("2 honesty B", "done", "HONESTY_B.txt", " ".join(
            line for line in text("HONESTY_B.txt").splitlines() if "nodes" in line or line == "PASS")),
        ("2 O and G", "done", "B_sums.txt", " | ".join(text("B_sums.txt").splitlines())),
        ("3 apply", "done", "apply_check.txt", text("apply_check.txt").strip()),
        ("3 proof 1 honesty P", "done", "HONESTY_P.txt", " ".join(
            line for line in text("HONESTY_P.txt").splitlines() if "nodes" in line or line == "PASS")),
        ("3 proof 2 off O", "done", "compare_off_O.txt", line_with("compare_off_O.txt", "differ")),
        ("3 proof 2 off G", "done", "compare_off_G.txt", line_with("compare_off_G.txt", "differ")),
        ("3 proof 3 on O", "done", "compare_on_O.txt", " ".join(
            line for line in text("compare_on_O.txt").splitlines() if line.startswith(("differ", "right_sum")))),
        ("3 proof 4 uci", "done", "uci_options.txt", " | ".join(text("uci_options.txt").splitlines())),
        ("3 proof 5 sanitizer", "done", "asan_sanitizer_lines.txt", " | ".join(
            text("asan_sanitizer_lines.txt").splitlines())),
        ("3 asan symbols", "done", "asan_G100_d10.meta", line_with("asan_G100_d10.meta", "nm_asan_count")),
        ("3 match", "done", "match_summary.txt", " | ".join(text("match_summary.txt").splitlines())),
        ("3 pgn", "done", "pgn_counts.txt", " | ".join(text("pgn_counts.txt").splitlines())),
        ("4 partner off", "done", "partner054_cmp_off_O.txt", line_with("partner054_cmp_off_O.txt", "differ")),
        ("4 partner on vs claim", "done", "partner054_cmp_on_vs_claim.txt", line_with(
            "partner054_cmp_on_vs_claim.txt", "differ")),
        ("4 partner on vs B", "done", "partner054_cmp_on_vs_B.txt", line_with(
            "partner054_cmp_on_vs_B.txt", "differ")),
        ("4 partner honesty", "done", "partner054_HONESTY.txt", " ".join(
            line for line in text("partner054_HONESTY.txt").splitlines() if line == "PASS" or line.startswith("bench") or line.startswith("perft"))),
        ("4 partner match", "done", "partner_match_summary.txt", " | ".join(
            text("partner_match_summary.txt").splitlines())),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {here.name}/{evidence} | {result}")


if __name__ == "__main__":
    main()
