#!/usr/bin/env python3
"""Read the raw evidence in this folder and print the report tables."""
from pathlib import Path

folder = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (folder / name).read_text(errors="replace").rstrip("\n")


def main() -> None:
    print("step | status | evidence | result")
    rows = [
        ("1 seat", "done", "SEAT.txt", text("SEAT.txt")),
        ("2 honesty B", "done", "HONESTY_B.txt", text("HONESTY_B.txt").splitlines()[-1]),
        ("2 O depth 12", "done", "compare_off_O.txt", "see proof 2"),
        ("2 G depth 12", "done", "compare_off_G.txt", "see proof 2"),
        ("3 prediction", "done", "prediction.txt", "committed before measuring P"),
        ("3 patch", "done", "apply_check_own.txt", text("apply_check_own.txt")),
        ("3 proof 1", "done", "HONESTY_p.txt", text("HONESTY_p.txt").splitlines()[-1]),
        ("3 proof 2 O", "done", "compare_off_O.txt", text("compare_off_O.txt").splitlines()[-1]),
        ("3 proof 2 G", "done", "compare_off_G.txt", text("compare_off_G.txt").splitlines()[-1]),
        ("3 proof 3", "done", "compare_on_O.txt", text("compare_on_O.txt").splitlines()[-2]),
        ("3 proof 4", "done", "uci_p.txt", "options listed below"),
        ("3 proof 5", "done", "asan_G100_d10.meta", "sanitizer_lines from meta"),
        ("3 match", "done", "match_og_summary.txt", text("match_og_summary.txt").splitlines()[1]),
        ("4 partner", "done", "partner003_on_vs_claim.txt", text("partner003_on_vs_claim.txt").splitlines()[-1]),
        ("4 partner match", "done", "partner003_match_summary.txt", text("partner003_match_summary.txt").splitlines()[1]),
    ]
    for step, status, evidence, result in rows:
        result = result.replace("|", "/")
        print(f"{step} | {status} | {evidence} | {result}")
    print()
    print("HONESTY_B")
    print(text("HONESTY_B.txt"))
    print()
    print("HONESTY_P")
    print(text("HONESTY_p.txt"))
    print()
    print("COMPARE_OFF_O")
    print(text("compare_off_O.txt"))
    print()
    print("COMPARE_OFF_G")
    print(text("compare_off_G.txt"))
    print()
    print("COMPARE_ON_O")
    print(text("compare_on_O.txt"))
    print()
    print("UCI_OPTIONS")
    for line in text("uci_p.txt").splitlines():
        if "IdeaS38_" in line or line.startswith("option name LmrSignedCorrection "):
            print(line)
    print()
    print("ASAN_META_LINES")
    for line in text("asan_G100_d10.meta").splitlines():
        if line.startswith("nm ") or line.startswith("sanitizer_lines"):
            print(line)
    print("ASAN_SCRATCH")
    print(text("asan_scratch.asan"))
    print()
    print("MATCH")
    print(text("match_og_summary.txt"))
    print()
    print("PARTNER_OFF")
    print(text("partner003_off_vs_B.txt"))
    print()
    print("PARTNER_ON")
    print(text("partner003_on_vs_claim.txt"))
    print()
    print("PARTNER_HONESTY")
    print(text("HONESTY_partner003.txt"))
    print()
    print("PARTNER_MATCH")
    print(text("partner003_match_summary.txt"))
    print()
    print("B_O_SUM_LINE")
    # First three and the sum are in the nodes file the harness wrote from the transcript.
    nodes = [int(x) for x in text("B_O_d12.nodes").split()]
    print(f"count={len(nodes)} sum={sum(nodes)} first3={nodes[0]},{nodes[1]},{nodes[2]}")
    gnodes = [int(x) for x in text("B_G_d12.nodes").split()]
    print(f"G count={len(gnodes)} sum={sum(gnodes)}")


if __name__ == "__main__":
    main()
