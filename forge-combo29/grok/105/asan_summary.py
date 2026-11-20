#!/usr/bin/env python3
"""Sanitizer proof: symbol count, clean run, and the deliberate fault."""
import pathlib
import subprocess

OUT = pathlib.Path(__file__).resolve().parent
CLEAN = pathlib.Path("/agent/repos/work/forge-combo29/build-asan/forge")
BUG = pathlib.Path("/tmp/asan-bug/build-asan/forge")


def asan_count(path: pathlib.Path) -> str:
    proc = subprocess.run(["nm", "-C", str(path)], text=True, capture_output=True, check=False)
    return str(sum(1 for line in proc.stdout.splitlines() if "__asan_" in line))


def hits(path: pathlib.Path) -> int:
    text = path.read_text(errors="replace")
    return text.count("ERROR: AddressSanitizer") + text.count("runtime error:")


def main() -> None:
    clean_n = asan_count(CLEAN)
    bug_n = asan_count(BUG)
    clean_hits = hits(OUT / "G_asan.raw")
    bug_text = (OUT / "asan_bug.raw").read_text(errors="replace")
    bug_line = next((line for line in bug_text.splitlines() if "ERROR: AddressSanitizer" in line), "MISSING")
    lines = [
        f"clean_exe={CLEAN}",
        f"clean_nm_asan={clean_n}",
        f"clean_sanitizer_lines={clean_hits}",
        f"bug_exe={BUG}",
        f"bug_nm_asan={bug_n}",
        f"bug_line={bug_line}",
    ]
    (OUT / "asan_summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    if int(clean_n) <= 0 or clean_hits != 0 or "heap-buffer-overflow" not in bug_line:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
