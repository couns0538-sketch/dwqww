#!/usr/bin/env python3
"""R3-1L: writes the configs file of one GitHub job (a subset of R3-1_selfplay/configs_final.json, unchanged
except the Syzygy path) and prints the exe keys (build_engines.sh names) the subset needs, one per line.

usage: job_configs.py <configs_final.json> <config names, comma separated> <syzygy dir> <out json>
"""
import json
import sys


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    src, names, tb, out = sys.argv[1:]
    with open(src, encoding="utf-8") as f:
        spec = json.load(f)
    by = {c["name"]: c for c in spec["configs"]}
    want = [n for n in names.split(",") if n]
    missing = [n for n in want if n not in by]
    if not want or missing:
        raise SystemExit(f"unknown or empty config list: {missing or names!r}")
    job = dict(spec)
    job["comment"] = f"R3-1L job subset of {src}: {','.join(want)} (only the syzygy path differs)"
    job["syzygy"] = tb
    job["configs"] = [by[n] for n in want]
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        json.dump(job, f, indent=1)
    keys = []
    for n in want:
        if by[n]["exe"] not in keys:
            keys.append(by[n]["exe"])
    print("\n".join(keys))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
