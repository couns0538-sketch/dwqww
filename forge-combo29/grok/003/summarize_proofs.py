#!/usr/bin/env python3
"""Read the proof files and print the numbers. Does not recompute searches."""
from pathlib import Path

root = Path(__file__).resolve().parent


def grab(path: Path, key: str) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1]
        if line.startswith(key + " "):
            return line.split(" ", 1)[1]
    return ""


def nodes_sum(name: str) -> str:
    lines = (root / name).read_text(encoding="utf-8").splitlines()
    return lines[-1]


def main() -> None:
    print("honesty_p")
    text = (root / "HONESTY_P.txt").read_text(encoding="utf-8")
    for key in ("bench11", "bench13", "bench16", "perft5"):
        for line in text.splitlines():
            if line.startswith(key + "="):
                print(line)
    print("uci")
    uci = (root / "uci_p.txt").read_text(encoding="utf-8").splitlines()
    for line in uci:
        if "IdeaS38" in line:
            print(line)
    print("compare_O_off")
    print((root / "compare_O_off.txt").read_text(encoding="utf-8").strip())
    print("compare_G_off")
    print((root / "compare_G_off.txt").read_text(encoding="utf-8").strip())
    print("compare_O_on")
    print((root / "compare_O_on.txt").read_text(encoding="utf-8").strip())
    print("asan_nm", (root / "asan_nm.txt").read_text(encoding="utf-8").strip())
    raw = (root / "asan_G100.raw").read_text(encoding="utf-8", errors="replace")
    print("asan_G100", nodes_sum("asan_G100.nodes"))
    print("asan_G100_sanitizer", sum(raw.count(m) for m in ("ERROR: AddressSanitizer", "runtime error:")))
    bug = (root / "asan_bug.raw").read_text(encoding="utf-8", errors="replace")
    print("asan_bug_heap", bug.count("heap-buffer-overflow"))
    print("asan_bug_error", bug.count("ERROR: AddressSanitizer"))
    print("apply", "see make_patch.sh output recorded in the commit of idea.patch.txt")


if __name__ == "__main__":
    main()
