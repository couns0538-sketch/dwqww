#!/usr/bin/env python3
"""Compare the partner build's O rows to exe B and to seat 064's own file."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEIRS = Path("/tmp/grok014/partner064_O_on.txt")


def rows(path: Path) -> list[tuple[str, str, str]]:
    out = []
    for line in path.read_text().splitlines():
        if line.startswith("SUM"):
            continue
        index, nodes, best, _fen = line.split("\t", 3)
        out.append((index, nodes, best))
    return out


def main() -> None:
    base = rows(HERE / "O_d12_B.txt")
    off = rows(HERE / "partner_O_off.txt")
    on = rows(HERE / "partner_O_on.txt")
    theirs = rows(THEIRS)
    print("partner off vs B differ", sum(a != b for a, b in zip(off, base)), "of", len(off))
    print("partner on vs seat 064 file differ", sum(a != b for a, b in zip(on, theirs)), "of", len(on))
    print("partner on sum", sum(int(x[1]) for x in on))
    print("seat 064 on sum", sum(int(x[1]) for x in theirs))


if __name__ == "__main__":
    main()
