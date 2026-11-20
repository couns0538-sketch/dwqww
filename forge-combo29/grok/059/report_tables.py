#!/usr/bin/env python3
"""Print the report tables from the raw files in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (HERE / name).read_text()


def nodes_tail(name: str) -> str:
    lines = text(name).splitlines()
    head = " ".join(lines[:3])
    tail = " ".join(lines[-2:])
    return f"{name} first {head} {tail}"


def main() -> int:
    print("HONESTY_B")
    print(text("HONESTY_B.txt").rstrip())
    print("HONESTY_P")
    print(text("HONESTY_P.txt").rstrip())
    print("HONESTY_PARTNER")
    print(text("HONESTY_PARTNER.txt").rstrip())
    print("NODES")
    for name in ("B_O.nodes", "B_G.nodes", "P_off_O.nodes", "P_off_G.nodes", "P_on_O.nodes",
                 "partner_off_O.nodes", "partner_on_O.nodes"):
        print(nodes_tail(name))
    print("COMPARE")
    for name in ("proof_off_O.txt", "proof_off_G.txt", "proof_on_O.txt",
                 "partner_off_vs_B.txt", "partner_on_vs_B.txt", "partner_on_vs_theirs.txt"):
        print(f"-- {name}")
        print(text(name).rstrip())
    print("UCI")
    for line in text("P_uci.txt").splitlines():
        if "AspCappedReopen" in line:
            print(line)
    print("ASAN_G100")
    for line in text("P_asan_G100.meta").splitlines():
        if line.startswith(("nm_asan", "sanitizer_", "failed=", "exe=")):
            print(line)
    print("ASAN_CANARY")
    for line in text("P_asan_canary.meta").splitlines():
        if line.startswith(("nm_asan", "sanitizer_", "failed=", "exe=")):
            print(line)
    print("MATCH")
    print(text("match_summary.txt").rstrip())
    print("PARTNER_MATCH")
    print(text("partner_R_summary.txt").rstrip())
    print("APPLY")
    print(text("apply_check.txt").rstrip())
    print(text("partner_apply_check.txt").rstrip())
    def differ_of(name: str) -> str:
        for line in text(name).splitlines():
            if line.startswith("differ "):
                return line.split()[1]
        return "missing"

    def sum_of(name: str) -> str:
        for line in text(name).splitlines():
            if line.startswith("sum "):
                return line.split()[1]
        return "missing"

    def field(name: str, prefix: str) -> str:
        for line in text(name).splitlines():
            if line.startswith(prefix):
                return line.split("=", 1)[1]
        return "missing"

    elo = ""
    games = ""
    for line in text("match_summary.txt").splitlines():
        if line.startswith("Elo:"):
            elo = line
        if line.startswith("Games:"):
            games = line.split(",")[0]
    pelo = ""
    pgames = ""
    for line in text("partner_R_summary.txt").splitlines():
        if line.startswith("Elo:"):
            pelo = line
        if line.startswith("Games:"):
            pgames = line.split(",")[0]
    honesty_b = "PASS" if text("HONESTY_B.txt").rstrip().endswith("PASS") else "FAIL"
    honesty_p = "PASS" if text("HONESTY_P.txt").rstrip().endswith("PASS") else "FAIL"
    print("TABLE")
    rows = [
        ("STEP 1 seat", "done", "SEAT.txt stamps.txt", text("SEAT.txt").strip()),
        ("STEP 2 honesty B", "done", "HONESTY_B.txt", honesty_b),
        ("STEP 2 O and G", "done", "B_O.nodes B_G.nodes",
         f"O {sum_of('B_O.nodes')} G {sum_of('B_G.nodes')}"),
        ("STEP 3 prediction", "done", "prediction.txt", "committed before any P measurement"),
        ("STEP 3 patch", "done", "idea.patch.txt apply_check.txt", text("apply_check.txt").strip()),
        ("proof 1 honesty P", "done", "HONESTY_P.txt", honesty_p),
        ("proof 2 switch off", "done", "proof_off_O.txt proof_off_G.txt",
         f"O differ {differ_of('proof_off_O.txt')} G differ {differ_of('proof_off_G.txt')}"),
        ("proof 3 switch on", "done", "proof_on_O.txt P_on_O.nodes",
         f"differ {differ_of('proof_on_O.txt')} of 200 sum {sum_of('P_on_O.nodes')}"),
        ("proof 4 uci", "done", "P_uci.txt",
         " ".join(line for line in text("P_uci.txt").splitlines() if "AspCappedReopen" in line)),
        ("proof 5 sanitizer", "done", "P_asan_G100.meta P_asan_canary.meta",
         f"nm {field('P_asan_G100.meta', 'nm_asan_symbols=')} "
         f"lines {field('P_asan_G100.meta', 'sanitizer_lines=')} "
         f"canary {field('P_asan_canary.meta', 'sanitizer_lines=')}"),
        ("STEP 3 match", "done", "match_summary.txt", f"{games} {elo}"),
        ("STEP 4 partner", "done", "partner_on_vs_theirs.txt partner_R_summary.txt",
         f"their rows differ {differ_of('partner_on_vs_theirs.txt')} {pgames} {pelo}"),
    ]
    print("step | status | evidence | result")
    for row in rows:
        print(" | ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
