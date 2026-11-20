#!/usr/bin/env python3
"""Print the proof numbers from the raw files in this directory. Nothing is typed."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def last_nodes(name: str) -> str:
    lines = (HERE / name).read_text().splitlines()
    hit = [ln.strip() for ln in lines if "nodes" in ln]
    return hit[-1] if hit else "MISSING"


def rows(name: str) -> list[tuple[str, str, str]]:
    out = []
    for line in (HERE / name).read_text().splitlines():
        if line.startswith("SUM"):
            continue
        index, nodes, best, _fen = line.split("\t", 3)
        out.append((index, nodes, best))
    return out


def sum_line(name: str) -> str:
    for line in (HERE / name).read_text().splitlines():
        if line.startswith("SUM"):
            return line
    return "MISSING"


def differ(a: str, b: str) -> tuple[int, int]:
    ra, rb = rows(a), rows(b)
    n = min(len(ra), len(rb))
    d = sum(ra[i] != rb[i] for i in range(n))
    return d, n


def main() -> None:
    print("honesty B")
    for tag in ("bench11", "bench13", "bench16", "perft5"):
        print(tag, last_nodes(f"{tag}_B.txt"))
    print("honesty P no setoption")
    for tag in ("bench11", "bench13", "bench16", "perft5"):
        print(tag, last_nodes(f"{tag}_P.txt"))
    print("uci IdeaS5 lines")
    for line in (HERE / "uci_P.txt").read_text().splitlines():
        if "IdeaS5" in line:
            print(line)
    for label, a, b in (
        ("O off vs B", "O_d12_B.txt", "O_d12_P_off.txt"),
        ("G off vs B", "G_d12_B.txt", "G_d12_P_off.txt"),
        ("O on vs B", "O_d12_B.txt", "O_d12_P_on.txt"),
    ):
        d, n = differ(a, b)
        print(f"{label} differ {d} of {n} {sum_line(a)} {sum_line(b)}")
    meta = (HERE / "asan_G100_d10.meta").read_text().splitlines()
    for line in meta:
        if line.startswith("nm_asan_count=") or line.startswith("sha256="):
            print("asan", line)
    print("asan G100", sum_line("asan_G100_d10.txt"))
    log = (HERE / "asan_G100_d10.txt.log").read_text()
    clean = sum(1 for ln in log.splitlines() if "ERROR: AddressSanitizer" in ln or "ERROR: UndefinedBehaviorSanitizer" in ln)
    print("asan clean error lines", clean)
    blog = (HERE / "asan_bug_special.txt.log").read_text().splitlines()
    hits = [ln for ln in blog if "ERROR: AddressSanitizer" in ln or "runtime error:" in ln]
    print("asan bug lines", len(hits))
    for ln in hits[:4]:
        print(ln)


if __name__ == "__main__":
    main()
