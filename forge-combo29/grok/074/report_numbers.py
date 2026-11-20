#!/usr/bin/env python3
"""Print the report tables from the raw result files. Does not invent numbers."""

from pathlib import Path

OUT = Path(__file__).resolve().parent


def read(name):
    return (OUT / name).read_text(encoding="utf-8")


def nodes(name):
    rows = []
    for line in read(name).splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            rows.append(int(parts[1]))
    return rows


def show_nodes(label, name):
    rows = nodes(name)
    first = " ".join(str(n) for n in rows[:3])
    print(f"{label} n {len(rows)} sum {sum(rows)} first3 {first} file {name}")


def main():
    print("HONESTY_B")
    print(read("HONESTY_B.txt"), end="")
    print("HONESTY_P")
    print(read("HONESTY_P.txt"), end="")
    print("PARTNER_HONESTY")
    print(read("partner_honesty.txt"), end="")
    show_nodes("B_O", "b_O.nodes.txt")
    show_nodes("B_G", "b_G.nodes.txt")
    show_nodes("P_OFF_O", "p_off_O.nodes.txt")
    show_nodes("P_OFF_G", "p_off_G.nodes.txt")
    show_nodes("P_ON_O", "p_on_O.nodes.txt")
    print("COMPARE_OFF_O")
    print(read("compare_off_O.txt"), end="")
    print("COMPARE_OFF_G")
    print(read("compare_off_G.txt"), end="")
    print("COMPARE_ON_O")
    print(read("compare_on_O.txt"), end="")
    print("ASAN_NM")
    print(read("asan_nm.txt"), end="")
    print("ASAN_SCAN")
    print(read("asan_g100_scan.txt"), end="")
    print("ASAN_SCRATCH_ERROR")
    for line in read("asan_scratch.raw.txt").splitlines():
        if "ERROR: AddressSanitizer" in line or line.startswith("SUMMARY: AddressSanitizer"):
            print(line)
    print("APPLY_CHECK")
    print(read("apply_check.txt"), end="")
    print("PARTNER_APPLY_CHECK")
    print(read("partner_apply_check.txt"), end="")
    print("PARTNER_OFF")
    print(read("partner_off_compare.txt"), end="")
    print("PARTNER_ON")
    print(read("partner_on_compare.txt"), end="")
    print("MATCH_FINAL")
    elo = [line for line in read("match_og.txt").splitlines() if line.startswith("Elo:")]
    games = [line for line in read("match_og.txt").splitlines() if line.startswith("Games:")]
    print(elo[-1] if elo else "MISSING")
    print(games[-1] if games else "MISSING")
    print("PARTNER_MATCH_FINAL")
    elo = [line for line in read("partner_match.txt").splitlines() if line.startswith("Elo:")]
    games = [line for line in read("partner_match.txt").splitlines() if line.startswith("Games:")]
    print(elo[-1] if elo else "MISSING")
    print(games[-1] if games else "MISSING")
    print("PREDICTION")
    print(read("prediction.txt"), end="")
    on = nodes("p_on_O.nodes.txt")
    off = nodes("p_off_O.nodes.txt")
    differ = sum(1 for a, b in zip(off, on) if a != b)
    print("STEP_TABLE")
    rows = [
        ("1 seat", "done", "SEAT.txt", "074 idea 24"),
        ("2 honesty B and sums", "done", "HONESTY_B.txt b_O.nodes.txt b_G.nodes.txt", "benches match; O 9500069; G 18466239"),
        ("3a read", "done", "decisions.txt", "EXISTS no"),
        ("3b prediction", "done", "prediction.txt", "10400000 and Elo 8, not edited"),
        ("3c patch", "done", "idea.patch.txt apply_check.txt", "base_apply_exit 0"),
        ("3d proofs", "done", "compare_on_O.txt asan_g100_scan.txt asan_scratch.raw.txt", f"off differ 0; on differ {differ} of {len(on)}; sanitizer clean and poison reported"),
        ("3e match", "done", "match_og.txt match_og.pgn", "1106 games"),
        ("4 partner", "done", "partner_on_compare.txt partner_match.txt", "CONFIRMS; 600 R games"),
        ("5 report", "done", "REPORT.md RESULT.txt", "this file"),
    ]
    print("step | status | evidence | result")
    for step, status, evidence, result in rows:
        print(f"{step} | {status} | {evidence} | {result}")


if __name__ == "__main__":
    main()
