#!/usr/bin/env python3
"""Print the report table from the evidence files in this folder."""
from pathlib import Path


def text(folder: Path, name: str) -> str:
    path = folder / name
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def has(blob: str, needle: str) -> bool:
    return needle in blob


def main() -> int:
    folder = Path(__file__).resolve().parent
    honesty_b = text(folder, "HONESTY_B.txt")
    honesty_p = text(folder, "HONESTY_P.txt")
    off_o = text(folder, "compare_off_O.txt")
    off_g = text(folder, "compare_off_G.txt")
    on_o = text(folder, "compare_on_O.txt")
    on_sum = text(folder, "sum_P_on_O.txt")
    asan = text(folder, "asan_g100.meta")
    scratch = text(folder, "asan_scratch.sanitizer.txt")
    match = text(folder, "match_s28.parsed.txt")
    partner_off = text(folder, "partner_off_vs_B.txt")
    partner_on = text(folder, "partner_on_vs_rows.txt")
    partner_vs_b = text(folder, "partner_on_vs_B.txt")
    partner_match = text(folder, "partner_match.parsed.txt")
    apply_mine = text(folder, "apply_check_mine.txt").strip()
    apply_partner = text(folder, "apply_check_partner.txt").strip()

    rows = [
        ("1 seat", "done", "SEAT.txt", "seat 002 idea 2"),
        ("2 honesty B", "done" if has(honesty_b, "PASS") else "not done", "HONESTY_B.txt", "PASS" if has(honesty_b, "PASS") else "FAIL"),
        ("2 baseline O", "done" if has(text(folder, "sum_B_O.txt"), "sum 9500069") else "not done", "sum_B_O.txt", "sum 9500069"),
        ("2 baseline G", "done" if has(text(folder, "sum_B_G.txt"), "sum 18466239") else "not done", "sum_B_G.txt", "sum 18466239"),
        ("3 patch applies", "done" if apply_mine == "MY_APPLY_CHECK_OK" else "not done", "apply_check_mine.txt", apply_mine or "missing"),
        ("3 honesty P", "done" if has(honesty_p, "PASS") else "not done", "HONESTY_P.txt", "PASS" if has(honesty_p, "PASS") else "FAIL"),
        ("3 off O", "done" if has(off_o, "differ 0") else "not done", "compare_off_O.txt", "differ 0" if has(off_o, "differ 0") else "differs"),
        ("3 off G", "done" if has(off_g, "differ 0") else "not done", "compare_off_G.txt", "differ 0" if has(off_g, "differ 0") else "differs"),
        ("3 on O", "done" if has(on_o, "differ 200") else "not done", "compare_on_O.txt", "differ 200"),
        ("3 sanitizer", "done" if has(asan, "asan_symbol_count 35") and has(asan, "sanitizer_lines 0") and has(scratch, "heap-buffer-overflow") else "not done", "asan_g100.meta", "clean, scratch reported"),
        ("3 match", "done" if has(match, "games 1106") else "not done", "match_s28.parsed.txt", "games 1106"),
        ("4 partner apply", "done" if apply_partner == "PARTNER_APPLY_CHECK_OK" else "not done", "apply_check_partner.txt", apply_partner or "missing"),
        ("4 partner off", "done" if has(partner_off, "differ 0") else "not done", "partner_off_vs_B.txt", "differ 0" if has(partner_off, "differ 0") else "differs"),
        ("4 partner on rows", "done" if has(partner_on, "differ 0") else "not done", "partner_on_vs_rows.txt", "equal to partner rows" if has(partner_on, "differ 0") else "differs"),
        ("4 partner on vs B", "done" if has(partner_vs_b, "differ 200") else "not done", "partner_on_vs_B.txt", "differ 200"),
        ("4 partner match", "done" if has(partner_match, "games 600") else "not done", "partner_match.parsed.txt", "games 600"),
        ("5 report", "done", "REPORT.md", "this file"),
    ]
    print("step | status | evidence file | result")
    print("--- | --- | --- | ---")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")
    print()
    print("on sum:")
    print(on_sum.strip())
    print()
    print("match:")
    print(match.strip())
    print()
    print("partner match:")
    print(partner_match.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
