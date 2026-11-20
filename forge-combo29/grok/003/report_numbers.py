#!/usr/bin/env python3
"""Print the report numbers from the raw files. Nothing here is typed by hand."""
from pathlib import Path

root = Path(__file__).resolve().parent


def last_result(path: Path) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    block = []
    current = []
    for line in lines:
        if line.startswith("Results of "):
            current = [line]
        elif current:
            current.append(line)
            if line.startswith("Games:"):
                block = current
                current = []
    print(f"file {path.name}")
    for line in block:
        print(line)


def honesty(name: str) -> None:
    print(f"file {name}")
    for line in (root / name).read_text(encoding="utf-8").splitlines():
        if line.startswith(("bench", "perft", "expect")):
            print(line)


def main() -> None:
    honesty("HONESTY_B.txt")
    honesty("HONESTY_P.txt")
    honesty("PARTNER_HONESTY.txt")
    for name in ("compare_O_off.txt", "compare_G_off.txt", "compare_O_on.txt",
                 "partner_compare_off.txt", "partner_compare_on.txt"):
        print(f"file {name}")
        print((root / name).read_text(encoding="utf-8").strip())
    print("asan_nm", (root / "asan_nm.txt").read_text(encoding="utf-8").strip())
    raw = (root / "asan_G100.raw").read_text(encoding="utf-8", errors="replace")
    bug = (root / "asan_bug.raw").read_text(encoding="utf-8", errors="replace")
    print("asan_G100_error", raw.count("ERROR: AddressSanitizer"))
    print("asan_G100_runtime", raw.count("runtime error:"))
    print("asan_G100", (root / "asan_G100.nodes").read_text(encoding="utf-8").splitlines()[-1])
    print("asan_bug_error", bug.count("ERROR: AddressSanitizer"))
    print("asan_bug_heap", bug.count("heap-buffer-overflow"))
    print("uci")
    for line in (root / "uci_p.txt").read_text(encoding="utf-8").splitlines():
        if "IdeaS38" in line:
            print(line)
    print("O_P_on", (root / "O_P_on.nodes").read_text(encoding="utf-8").splitlines()[-1])
    print("prediction")
    print((root / "prediction.txt").read_text(encoding="utf-8").strip())
    last_result(root / "match.txt")
    last_result(root / "partner_match.txt")
    def tail(name: str) -> str:
        return (root / name).read_text(encoding="utf-8").strip().splitlines()[-1]

    def differ_line(name: str) -> str:
        for line in (root / name).read_text(encoding="utf-8").splitlines():
            if line.startswith("differ "):
                return line
        return ""

    print("step | status | evidence | result")
    rows = [
        ("1 seat", "done", "SEAT.txt", (root / "SEAT.txt").read_text(encoding="utf-8").strip()),
        ("2 honesty B", "done", "HONESTY_B.txt", " ".join(
            line.split("=", 1)[1] for line in (root / "HONESTY_B.txt").read_text(encoding="utf-8").splitlines()
            if line.startswith(("bench", "perft")) and not line.startswith("expect"))),
        ("2 baseline O", "done", "O_B.nodes", tail("O_B.nodes")),
        ("2 baseline G", "done", "G_B.nodes", tail("G_B.nodes")),
        ("3 prediction", "done", "prediction.txt", "committed before measuring exe P"),
        ("3 proof 1", "done", "HONESTY_P.txt", " ".join(
            line.split("=", 1)[1] for line in (root / "HONESTY_P.txt").read_text(encoding="utf-8").splitlines()
            if line.startswith(("bench", "perft")) and not line.startswith("expect"))),
        ("3 proof 2 O off", "done", "compare_O_off.txt", differ_line("compare_O_off.txt")),
        ("3 proof 2 G off", "done", "compare_G_off.txt", differ_line("compare_G_off.txt")),
        ("3 proof 3 O on", "done", "compare_O_on.txt", differ_line("compare_O_on.txt") + " " + tail("O_P_on.nodes")),
        ("3 proof 4", "done", "uci_p.txt", "IdeaS38 lines printed above"),
        ("3 proof 5", "done", "asan_nm.txt asan_G100.raw asan_bug.raw",
         f"nm {(root / 'asan_nm.txt').read_text(encoding='utf-8').strip()} "
         f"G100_errors {raw.count('ERROR: AddressSanitizer')} "
         f"bug_errors {bug.count('ERROR: AddressSanitizer')}"),
        ("3 match", "done", "match.txt", "last Results block above"),
        ("4 partner rows", "done", "partner_compare_off.txt partner_compare_on.txt",
         differ_line("partner_compare_off.txt") + " / " + differ_line("partner_compare_on.txt")),
        ("4 partner match", "done", "partner_match.txt", "last Results block above"),
        ("5 report", "done", "REPORT.md RESULT.txt", "written with this script's output"),
    ]
    for row in rows:
        print(" | ".join(row))


if __name__ == "__main__":
    main()
