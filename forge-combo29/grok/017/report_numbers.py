#!/usr/bin/env python3
"""Print the numeric tables for REPORT.md from the saved raw files."""
from pathlib import Path

here = Path(__file__).resolve().parent


def head(name, n=20):
    path = here / name
    print(f"--- {name} ---")
    if not path.exists():
        print("MISSING")
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[:n]:
        print(line)


def main():
    for name in (
        "HONESTY_B.txt",
        "HONESTY_P.txt",
        "B_O_summary.txt",
        "B_G_summary.txt",
        "compare_off_O.txt",
        "compare_off_G.txt",
        "compare_on_O.txt",
        "P_on_O_summary.txt",
        "probe_off_d12_summary.txt",
        "probe_on_d12_summary.txt",
        "match_OG_summary.txt",
        "compare_partner_067_off.txt",
        "compare_partner_067_on_vs_B.txt",
        "compare_partner_067_on_vs_theirs.txt",
        "match_partner_067_summary.txt",
        "partner_067_cmp_O_off.txt",
        "partner_067_cmp_O_on.txt",
        "partner_067_HONESTY_P.txt",
    ):
        head(name, 12)
    meta = (here / "raw_asan_G100_d10.txt.meta").read_text().splitlines()
    print("--- raw_asan_G100_d10.txt.meta nm ---")
    for i, line in enumerate(meta):
        if "nm -C" in line:
            print(line)
            print(meta[i + 1] if i + 1 < len(meta) else "")
    err = here / "raw_asan_G100_d10.txt.err"
    scratch = here / "raw_asan_scratch.txt.err"
    print(f"asan_err_bytes {err.stat().st_size}")
    print("--- scratch sanitizer line ---")
    for line in scratch.read_text(errors="replace").splitlines():
        if "runtime error" in line or "ERROR" in line or "Sanitizer" in line:
            print(line)
            break
    print("--- step table ---")
    rows = [
        ("STEP 1 seat", "done", "SEAT.txt", "seat 017 idea 17"),
        ("STEP 2 honesty B", "done", "HONESTY_B.txt", "312866 862329 3024920 4865609"),
        ("STEP 2 known sums", "done", "B_O_summary.txt B_G_summary.txt", "O 9500069 G 18466239"),
        ("STEP 3 prediction", "done", "prediction.txt", "committed before measuring P"),
        ("STEP 3 patch applies", "done", "idea.patch.txt", "git apply --check"),
        ("proof 1 honesty P", "done", "HONESTY_P.txt", "same four node counts"),
        ("proof 2 switch off", "done", "compare_off_O.txt compare_off_G.txt", "0 of 200 and 0 of 353"),
        ("proof 3 switch on", "done", "compare_on_O.txt", "0 of 200"),
        ("proof 4 uci options", "done", "uci_P.txt", "IdeaS15 false, IdeaS15_MinPieces 8"),
        ("proof 5 sanitizer", "done", "raw_asan_G100_d10.txt.meta raw_asan_scratch.txt.err", "nm 35, clean stderr, scratch reported"),
        ("STEP 3 match", "done", "match_OG_summary.txt", "elo -0.63 +/- 5.84 games 1106"),
        ("STEP 4 partner", "done", "compare_partner_067_off.txt compare_partner_067_on_vs_theirs.txt match_partner_067_summary.txt", "067 CONFIRMS on the repeated proofs"),
        ("handoff minute 60", "done", "gate_notes.txt", "no FABLE_TO_grok file"),
    ]
    print("step | status | evidence | result")
    for row in rows:
        print(" | ".join(row))


if __name__ == "__main__":
    main()
