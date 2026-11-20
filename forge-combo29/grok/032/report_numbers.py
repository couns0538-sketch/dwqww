#!/usr/bin/env python3
"""Read this seat's raw result files and print the report numbers."""
from pathlib import Path

OUT = Path(__file__).resolve().parent


def text(name: str) -> str:
    return (OUT / name).read_text()


def main() -> None:
    print("HONESTY_B")
    print(text("HONESTY_B.txt").rstrip())
    print("HONESTY_P")
    print(text("HONESTY_P.txt").rstrip())
    print("COMPARE_OFF_O")
    print(text("compare_off_O.txt").rstrip())
    print("COMPARE_OFF_G")
    print(text("compare_off_G.txt").rstrip())
    print("COMPARE_ON_O")
    print(text("compare_on_O.txt").rstrip())
    print("UCI")
    print(text("uci_options.meta").rstrip())
    print("ASAN_META")
    for line in text("ASAN_G100.meta").splitlines():
        if line.startswith("nm_") or line.startswith("sanitizer_") or line.startswith("exe=") or line.startswith("positions") or line.startswith("depth="):
            print(line)
    print(text("ASAN_G100.sum").rstrip())
    print("ASAN_BUG")
    print(text("ASAN_BUG.meta").rstrip())
    print("APPLY")
    print(text("apply_check.txt").rstrip())
    print("MATCH")
    print(text("match_og.log")[text("match_og.log").rfind("Results of ") :].split("Finished match")[0].rstrip())
    print("PREDICTION")
    print(text("prediction.txt").rstrip())


if __name__ == "__main__":
    main()
