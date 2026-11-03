#!/usr/bin/env python3
"""sort_normalized.py - Opus R14-B item 2: put Astra normalized JSONL rows into game order for relabel2.py (own code).

Astra's `convert_forge.py OUT --selfplay ... --keep-result` writes `train.metadata.jsonl` / `val.metadata.jsonl`
shuffled (and split by position); `relabel2.py prepare --normalized` needs rows in source order to find games. This
tool reads one or more such files, sorts all rows by (source, source_row) and writes them to a NEW file; each line is
copied unchanged (no parsing beyond the two keys) except that a CRLF line end becomes LF and a leading BOM is dropped.
The keys must have the types relabel2.py accepts (source a string, source_row an integer).
Holds the input in memory (about 2.2x the input size); before reading it checks that the PC keeps at least
--min-free-ram-gb free (default 8: the crew's RAM guards stop training below 6-7 GB) and refuses otherwise (exit 2):
then split the input by source and sort each part (relabel2 takes several files when they are in order together).
Exit 0 = OUT written; 2 = bad usage or input (a damaged line, no rows, duplicate (source, source_row), an existing
OUT or OUT.part, too little RAM): nothing is written then.

usage: python -I -B sort_normalized.py [--min-free-ram-gb 8] OUT.jsonl IN.jsonl [IN2.jsonl ...]
"""

import ctypes
import json
import math
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


def refuse(msg) -> int:
    print(msg, file=sys.stderr)
    return 2


def main(argv) -> int:
    floor = 8.0
    if len(argv) > 1 and (argv[1] == "--min-free-ram-gb" or argv[1].startswith("--min-free-ram-gb=")):
        if "=" in argv[1]:
            value, argv = argv[1].partition("=")[2], argv[:1] + argv[2:]
        else:
            value, argv = (argv[2] if len(argv) > 2 else ""), argv[:1] + argv[3:]
        try:
            floor = float(value)
        except ValueError:
            floor = math.nan
        if not math.isfinite(floor) or floor < 0:  # nan used to switch the RAM check off (bug hunt #14)
            return refuse(f"--min-free-ram-gb needs a number of GB >= 0, not '{value}'")
    # a misspelt option used to become OUT or an input (bug hunt #14); file names never start with '-'
    bad = [x for x in argv[1:] if x.startswith("-")]
    if bad or len(argv) < 3:
        print(__doc__)
        if bad and bad[0] not in ("-h", "--help"):
            print(f"unknown option {bad[0]} (options come before OUT)", file=sys.stderr)
        return 2
    out, inputs = argv[1], argv[2:]
    tmp = out + ".part"
    if os.path.exists(out):
        return refuse(f"refusing existing {out}")
    if os.path.exists(tmp):  # left by an interrupted run; this tool never deletes or overwrites
        return refuse(f"refusing: {tmp} exists (left by an interrupted run?) - move it aside first")
    if not os.path.isdir(os.path.dirname(os.path.abspath(out))):
        return refuse(f"{out}: the output folder does not exist")
    for path in inputs:
        if not os.path.isfile(path):
            return refuse(f"{path}: input file not found")
    need = RAM_PER_INPUT_BYTE * sum(os.path.getsize(p) for p in inputs) / 2 ** 30
    free = free_ram_gb()
    if free is not None and free - need < floor:
        return refuse(f"sorting these inputs needs about {need:.1f} GB of RAM; {free:.1f} GB are free and {floor:g} GB "
                      f"must stay free (--min-free-ram-gb; the crew's RAM guards): split the input by source and sort "
                      f"each part")
    rows = []
    for path in inputs:
        with open(path, "rb") as fh:
            for n, raw in enumerate(fh, 1):
                try:  # bytes, decoded per line: a bad byte gives its line number, not a traceback (bug hunt #14)
                    line = raw.decode("utf-8-sig" if n == 1 else "utf-8")
                except UnicodeDecodeError as e:
                    return refuse(f"{path}:{n}: not UTF-8 text: {e}")
                if line.endswith("\r\n"):
                    line = line[:-2] + "\n"
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                    key = (r["source"], r["source_row"])
                    if type(key[0]) is not str or type(key[1]) is not int:  # the types relabel2.py accepts
                        raise TypeError(f"source must be a string and source_row an integer, not {key!r}")
                except (ValueError, KeyError, TypeError) as e:
                    return refuse(f"{path}:{n}: not a normalized self-play row with source / integer source_row: {e}")
                rows.append((key, line if line.endswith("\n") else line + "\n"))
    if not rows:  # an empty input used to give an empty OUT and exit 0 (bug hunt #14)
        return refuse(f"no rows in {', '.join(inputs)}: nothing written")
    rows.sort(key=lambda t: t[0])
    for (a, _), (b, _) in zip(rows, rows[1:]):
        if a == b:
            return refuse(f"duplicate source row {a}")
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
