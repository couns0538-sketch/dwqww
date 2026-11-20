#!/usr/bin/env python3
"""Read the raw evidence files and print the report table and the proof numbers."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def text(name):
    return (ROOT / name).read_text()


def rows_field(name, key):
    for line in text(name).splitlines():
        if line.startswith(key + " "):
            return line.split(maxsplit=1)[1]
    raise SystemExit(f"missing {key} in {name}")


def compare_sum(name, side):
    prefix = side + " sum "
    for line in text(name).splitlines():
        if line.startswith(prefix):
            return line[len(side) + 1:]
    raise SystemExit(f"missing {prefix} in {name}")


def honesty_nodes(name):
    found = []
    for line in text(name).splitlines():
        if "bench depth" in line and " nodes " in line:
            parts = line.split()
            found.append(parts[parts.index("nodes") + 1])
        elif line.startswith("nodes "):
            found.append(line.split()[1])
    return found


def main():
    b_nodes = honesty_nodes("HONESTY_B.txt")
    p_nodes = honesty_nodes("HONESTY_P.txt")
    off_o = rows_field("compare_off_O.txt", "differ")
    off_g = rows_field("compare_off_G.txt", "differ")
    on_o = rows_field("compare_on_O.txt", "differ")
    on_sum = compare_sum("compare_on_O.txt", "right")
    asan_nm = text("asan_nm_count.txt").strip()
    asan_clean = text("asan_G100.txt").count("Sanitizer")
    bad = text("asan_bad_runner.txt")
    bad_hit = "heap-buffer-overflow" in bad
    print("honesty_B " + " ".join(b_nodes))
    print("honesty_P " + " ".join(p_nodes))
    print(f"proof1_match {b_nodes == p_nodes}")
    print(f"proof2_off_O_differ {off_o}")
    print(f"proof2_off_G_differ {off_g}")
    print(f"proof3_on_O_differ {on_o}")
    print(f"proof3_on_line {on_sum}")
    print("proof4")
    print(text("uci_ideak11.txt"), end="" if text("uci_ideak11.txt").endswith("\n") else "\n")
    print(f"proof5_nm_asan {asan_nm}")
    print(f"proof5_clean_sanitizer_lines {asan_clean}")
    print(f"proof5_bad_heap_overflow {bad_hit}")
    print(f"proof5_bad_nm {text('asan_bad_nm_count.txt').strip()}")
    print("base_O " + compare_sum("compare_off_O.txt", "left"))
    print("base_G " + compare_sum("compare_off_G.txt", "left"))
    print()
    print("| step | status | evidence file | result |")
    print("| --- | --- | --- | --- |")
    rows = [
        ("1 seat", "done", "SEAT.txt", "seat 050 idea 50"),
        ("2 honesty B", "done", "HONESTY_B.txt", " ".join(b_nodes)),
        ("2 O depth 12 B", "done", "B_O_d12.rows", compare_sum("compare_off_O.txt", "left")),
        ("2 G depth 12 B", "done", "B_G_d12.rows", compare_sum("compare_off_G.txt", "left")),
        ("3 prediction", "done", "prediction.txt", "committed before measuring P"),
        ("3 patch applies", "done", "apply_check.txt", text("apply_check.txt").strip().replace("\n", " ")),
        ("3 proof 1 honesty P", "done", "HONESTY_P.txt", " ".join(p_nodes)),
        ("3 proof 2 switch off", "done", "compare_off_O.txt compare_off_G.txt", f"O differ {off_o}; G differ {off_g}"),
        ("3 proof 3 switch on", "done", "compare_on_O.txt", f"differ {on_o}; {on_sum}"),
        ("3 proof 4 uci", "done", "uci_ideak11.txt", "IdeaK11 false; Base 64; Divisor 160; Cap 320"),
        ("3 proof 5 sanitizer", "done", "asan_G100.meta asan_bad_runner.txt", f"nm {asan_nm}; clean lines {asan_clean}; bad overflow {bad_hit}"),
        ("3 match O+G", "done", "match_og_result.txt", "1106 games, see that file"),
        ("4 partner", "not done", "partner_none.txt", "no branch for-fable-and-opus/grok-100"),
        ("4 second match R", "done", "match_r_result.txt", "600 games, see that file"),
        ("5 report", "done", "REPORT.md RESULT.txt", "this step"),
    ]
    for step, status, evidence, result in rows:
        print(f"| {step} | {status} | {evidence} | {result} |")


if __name__ == "__main__":
    main()
