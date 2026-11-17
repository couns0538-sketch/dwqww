#!/usr/bin/env python3
"""Coverage check: does the walk reach every key in the compiled-in book?

If it does, the soundness audit in q7_soundness.py is a complete audit of the
book rather than a sample. If it does not, the unreached keys are listed so the
report can say exactly what was not tested.

Inputs:
  /tmp/book_full.txt   TSV from probe_book (FEN, KEY, PLY, MOVES)
  src/book_data.inc    the compiled book, parsed for BookKeys[]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def book_keys(inc: Path) -> list[int]:
    text = inc.read_text()
    m = re.search(r"BookKeys\[(\d+)\]\s*=\s*\{(.*?)\};", text, re.S)
    if not m:
        raise SystemExit(f"no BookKeys array in {inc}")
    count = int(m.group(1))
    body = m.group(2)
    values = [int(tok.rstrip("ULL"), 16) for tok in re.findall(r"0x[0-9a-fA-F]+ULL", body)]
    if len(values) != count:
        raise SystemExit(f"BookEntryCount says {count}, array has {len(values)}")
    return values


def probe_keys(tsv: Path) -> tuple[list[int], list[int]]:
    """Return (keys with book moves, keys reached with no book moves)."""
    in_book: list[int] = []
    empty: list[int] = []
    seen_header = False
    for line in tsv.read_text().splitlines():
        if line.startswith("FEN\t"):
            seen_header = True
            continue
        if not seen_header or not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        key = int(parts[1], 16)
        moves = parts[3] if len(parts) > 3 else ""
        (in_book if moves else empty).append(key)
    return in_book, empty


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default="/tmp/book_full.txt")
    ap.add_argument("--inc", default="src/book_data.inc")
    args = ap.parse_args()

    declared = book_keys(Path(args.inc))
    in_book, empty = probe_keys(Path(args.tsv))
    reached = in_book + empty

    declared_set = set(declared)
    reached_set = set(reached)
    with_moves = set(in_book)

    print(f"book entries (BookKeys): {len(declared)}")
    print(f"distinct keys in book:   {len(declared_set)}")
    print(f"positions reached by walk: {len(reached_set)} "
          f"({len(with_moves)} with book moves, {len(set(empty))} without)")
    missing = declared_set - with_moves
    extra = with_moves - declared_set
    print(f"book keys never reached: {len(missing)}/{len(declared_set)}")
    print(f"reached keys not in book: {len(extra)}/{len(with_moves)}")

    if missing:
        print("\nunreached keys:")
        for key in sorted(missing)[:20]:
            print(f"  {key:016x}")
    if extra:
        print("\nunexpected keys (walk found a key the book does not have, which "
              "would mean the polyglot key disagrees with itself):")
        for key in sorted(extra)[:20]:
            print(f"  {key:016x}")

    ok = not missing and not extra
    print("\nCOVERAGE " + ("COMPLETE: the soundness audit spans every book key"
                           if ok else "INCOMPLETE: see the lists above"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
