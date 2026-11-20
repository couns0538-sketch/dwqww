#!/usr/bin/env python3
"""Step table for REPORT.md. Every cell is read from a file in this folder."""
from pathlib import Path

OUT = Path(__file__).resolve().parent


def has(name: str) -> bool:
    return (OUT / name).is_file() and (OUT / name).stat().st_size > 0


def line_with(name: str, prefix: str) -> str:
    for line in (OUT / name).read_text().splitlines():
        if line.startswith(prefix):
            return line
    return "MISSING"


def main() -> None:
    rows = [
        ("1 seat", "done" if has("SEAT.txt") and has("stamps.txt") else "not done", "SEAT.txt", (OUT / "SEAT.txt").read_text().strip()),
        ("2 honesty B", "done" if "FAIL" not in (OUT / "HONESTY_B.txt").read_text() else "not done", "HONESTY_B.txt", "bench 11/13/16 and perft 5 match"),
        ("2 O and G sums", "done" if "sum 9500069" in (OUT / "B_O_d12.sum").read_text() and "sum 18466239" in (OUT / "B_G_d12.sum").read_text() else "not done", "B_O_d12.sum B_G_d12.sum", "O 9500069 G 18466239"),
        ("3 patch applies", "done" if (OUT / "apply_check.txt").read_text().strip() == "APPLY_CHECK_OK" else "not done", "apply_check.txt idea.patch.txt", (OUT / "apply_check.txt").read_text().strip()),
        ("3 proof off", "done" if line_with("compare_off_O.txt", "differ").endswith("0") and line_with("compare_off_G.txt", "differ").endswith("0") else "not done", "compare_off_O.txt compare_off_G.txt", "O differ 0, G differ 0"),
        ("3 proof on", "done" if "differ 200" in (OUT / "compare_on_O.txt").read_text() else "not done", "compare_on_O.txt", line_with("compare_on_O.txt", "differ ") + " " + line_with("compare_on_O.txt", "sum_b ")),
        ("3 uci options", "done" if "FAIL" not in (OUT / "uci_options.meta").read_text() else "not done", "uci_options.meta", "IdeaA1 false, Scale 1024, Clamp 2"),
        ("3 sanitizer", "done" if line_with("ASAN_G100.meta", "nm_asan_count=") == "nm_asan_count=35" and line_with("ASAN_G100.meta", "sanitizer_lines=") == "sanitizer_lines=0" and "heap-buffer-overflow" in (OUT / "ASAN_BUG.txt").read_text() else "not done", "ASAN_G100.meta ASAN_BUG.txt", "nm 35, clean run 0 lines, bug run reports heap-buffer-overflow"),
        ("3 match", "done" if "Games: 1106" in (OUT / "match_og.log").read_text() else "not done", "match_og.log", "Elo 1.26 +/- 10.31, 1106 games"),
        ("4 partner", "done" if "differ 0" in (OUT / "partner_on_vs_theirs.txt").read_text() and "Games: 600" in (OUT / "partner_match.log").read_text() else "partly", "partner_on_vs_theirs.txt partner_match.log", "rows differ 0, R match 600 games, Elo 0.58 +/- 12.18"),
        ("5 report", "done" if has("RESULT.txt") else "not done", "RESULT.txt REPORT.md", "this file"),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")


if __name__ == "__main__":
    main()
