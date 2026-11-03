#!/usr/bin/env python3
"""sort_normalized.py - Opus R14-B item 2: put Astra normalized JSONL rows into game order for relabel2.py (own code).

Astra's `convert_forge.py OUT --selfplay ... --keep-result` writes `train.metadata.jsonl` / `val.metadata.jsonl`
shuffled (and split by position); `relabel2.py prepare --normalized` needs rows in source order to find games. This
tool reads one or more such files, sorts all rows by (source, source_row) and writes them to a NEW file, unchanged
byte for byte (no parsing beyond the two keys). Duplicate (source, source_row) pairs stop it with exit 2.
Holds the input in memory (about 2.2x the input size); before reading it checks that the PC keeps at least
--min-free-ram-gb free (default 8: the crew's RAM guards stop training below 6-7 GB) and refuses otherwise (exit 2):
then split the input by source and sort each part (relabel2 takes several files when they are in order together).

usage: python -I -B sort_normalized.py [--min-free-ram-gb 8] OUT.jsonl IN.jsonl [IN2.jsonl ...]
"""

import ctypes
import json
import os
import sys

RAM_PER_INPUT_BYTE = 2.2  # Python str per line + key tuple + list slot, measured order of magnitude (~1 GB / 2.5M rows)


def free_ram_gb():
    """Available physical memory in GiB (Windows); None elsewhere."""
    if os.name != "nt":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    ms = MemoryStatus()
    ms.dwLength = ctypes.sizeof(MemoryStatus)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms)):
        return None
    return ms.ullAvailPhys / 2 ** 30


def main(argv) -> int:
    floor = 8.0
    if len(argv) > 2 and argv[1] == "--min-free-ram-gb":
        try:
            floor = float(argv[2])
        except ValueError:
            print(__doc__)
            return 2
        argv = argv[:1] + argv[3:]
    if len(argv) < 3:
        print(__doc__)
        return 2
    out, inputs = argv[1], argv[2:]
    if os.path.exists(out):
        print(f"refusing existing {out}", file=sys.stderr)
        return 2
    for path in inputs:
        if not os.path.isfile(path):
            print(f"{path}: input file not found", file=sys.stderr)
            return 2
    need = RAM_PER_INPUT_BYTE * sum(os.path.getsize(p) for p in inputs) / 2 ** 30
    free = free_ram_gb()
    if free is not None and free - need < floor:
        print(f"sorting these inputs needs about {need:.1f} GB of RAM; {free:.1f} GB are free and {floor:g} GB must stay "
              f"free (--min-free-ram-gb; the crew's RAM guards): split the input by source and sort each part",
              file=sys.stderr)
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
