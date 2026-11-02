#!/usr/bin/env python3
"""sort_normalized.py - Opus R14-B item 2: put Astra normalized JSONL rows into game order for relabel2.py (own code).

Astra's `convert_forge.py OUT --selfplay ... --keep-result` writes `train.metadata.jsonl` / `val.metadata.jsonl`
shuffled (and split by position); `relabel2.py prepare --normalized` needs rows in source order to find games. This
tool reads one or more such files, sorts all rows by (source, source_row) and writes them to a NEW file, unchanged
byte for byte (no parsing beyond the two keys). Duplicate (source, source_row) pairs stop it with exit 2.
Holds the input in memory (about 1 GB per ~2.5M rows); split bigger inputs by source.

usage: python -I -B sort_normalized.py OUT.jsonl IN.jsonl [IN2.jsonl ...]
"""

import json
import os
import sys


def main(argv) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    out, inputs = argv[1], argv[2:]
    if os.path.exists(out):
        print(f"refusing existing {out}", file=sys.stderr)
        return 2
    rows = []
    for path in inputs:
        with open(path, encoding="utf-8-sig") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    key = (str(r["source"]), int(r["source_row"]))
                except (ValueError, KeyError, TypeError) as e:
                    print(f"{path}:{n}: not a normalized self-play row with source / integer source_row: {e}",
                          file=sys.stderr)
                    return 2
                rows.append((key, line if line.endswith("\n") else line + "\n"))
    rows.sort(key=lambda t: t[0])
    for (a, _), (b, _) in zip(rows, rows[1:]):
        if a == b:
            print(f"duplicate source row {a}", file=sys.stderr)
            return 2
    tmp = out + ".part"
    with open(tmp, "x", encoding="utf-8", newline="\n") as fh:
        for _, line in rows:
            fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())
    os.rename(tmp, out)
    print(f"{len(rows)} rows from {len(inputs)} file(s) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
