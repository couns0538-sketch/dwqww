#!/usr/bin/env python3
"""Read this seat's raw result files and print the report table."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text()


def line_with(name: str, prefix: str) -> str:
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line
    return "MISSING " + prefix


def meta_value(name: str, key: str) -> str:
    for line in text(name).splitlines():
        if line.startswith(key + " "):
            return line.split(" ", 1)[1]
    return "MISSING"


def main() -> int:
    print("honesty_B")
    for line in text("HONESTY_B.txt").splitlines():
        print(line)
    print("honesty_P")
    for line in text("HONESTY_P.txt").splitlines():
        print(line)
    print("baseline")
    print(text("B_OG_sums.txt"), end="")
    print("off_O")
    print(text("off_O_vs_B.txt"), end="")
    print("off_G")
    print(text("off_G_vs_B.txt"), end="")
    print("on_O")
    print(line_with("on_O_vs_B.txt", "positions"))
    print(line_with("on_O_vs_B.txt", "left_sum"))
    print(line_with("on_O_vs_B.txt", "right_sum"))
    print(line_with("on_O_vs_B.txt", "differ"))
    print("uci")
    for line in text("uci_p.txt").splitlines():
        if line.startswith("id name") or "IdeaS22" in line:
            print(line)
    print("asan_good", "symbols", meta_value("asan_G100.meta", "nm_asan_symbol_lines"),
          "sanitizer_lines", meta_value("asan_G100.meta", "sanitizer_lines"),
          "done", meta_value("asan_G100.meta", "positions_done"))
    print("asan_scratch", "symbols", meta_value("asan_scratch.meta", "nm_asan_symbol_lines"),
          "sanitizer_lines", meta_value("asan_scratch.meta", "sanitizer_lines"))
    for line in text("asan_scratch.meta").splitlines():
        if "runtime error" in line or "AddressSanitizer" in line:
            print(line)
    print("match")
    print(text("match_og_final.txt"), end="")
    print("partner_honesty")
    print(line_with("partner_HONESTY.txt", "bench 11"))
    print(line_with("partner_HONESTY.txt", "bench 13"))
    print(line_with("partner_HONESTY.txt", "bench 16"))
    print(line_with("partner_HONESTY.txt", "go perft 5"))
    print(line_with("partner_HONESTY.txt", "PASS") if "PASS" in text("partner_HONESTY.txt") else "FAIL")
    print("partner_off")
    print(line_with("partner_off_vs_B.txt", "differ"))
    print(line_with("partner_off_vs_B.txt", "right_sum"))
    print("partner_on_vs_B")
    print(line_with("partner_on_vs_B.txt", "differ"))
    print(line_with("partner_on_vs_B.txt", "right_sum"))
    print("partner_on_vs_claim")
    print(text("partner_on_vs_claim.txt"), end="")
    print("partner_match")
    print(text("partner_match_final.txt"), end="")
    rows = [
        ("1 seat", "done", "SEAT.txt", "020 idea 20"),
        ("2 honesty B", "done", "HONESTY_B.txt", "PASS"),
        ("2 baseline O G", "done", "B_OG_sums.txt", "9500069 and 18466239"),
        ("3 prediction", "done", "prediction.txt", "pushed before measuring P"),
        ("3 patch applies", "done", "idea.patch.txt", "git apply --check passed"),
        ("3 proof 1 honesty P", "done", "HONESTY_P.txt", "PASS"),
        ("3 proof 2 off", "done", "off_O_vs_B.txt off_G_vs_B.txt", "differ 0 and differ 0"),
        ("3 proof 3 on", "done", "on_O_vs_B.txt", "differ 194 sum 9571899"),
        ("3 proof 4 uci", "done", "uci_p.txt", "IdeaS22 false, IdeaS22_Plies 1"),
        ("3 proof 5 sanitizer", "done", "asan_G100.meta asan_scratch.meta", "0 lines, scratch 1 line, asan symbols 35"),
        ("3 match", "done", "match_og_final.txt", "1106 games Elo -5.65 +/- 9.85"),
        ("4 partner", "done", "partner_on_vs_claim.txt partner_match_final.txt", "CONFIRMS"),
        ("5 report", "done", "REPORT.md RESULT.txt", "this file"),
    ]
    print("step | status | evidence | result")
    for row in rows:
        print(" | ".join(row))
    return 0


if __name__ == "__main__":
    main()
