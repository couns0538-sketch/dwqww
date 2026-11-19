#!/usr/bin/env python3
"""Print the forty Job 39 spin declarations from each fresh UCI reply."""

import argparse
from pathlib import Path
import re

from generate_draws39 import NAMES


OPTION = re.compile(r"option name (.+?) type (\S+)(?: .*)?")


def audit(build, path):
    print(f"{build} UCI spin options")
    lines = path.read_text(encoding="utf-8").splitlines()
    declarations = {}
    for line in lines:
        if match := OPTION.fullmatch(line):
            name, kind = match.groups()
            declarations.setdefault(name, []).append((kind, line))

    errors = []
    if lines.count("uciok") != 1:
        errors.append(f"expected one uciok, got {lines.count('uciok')}")
    for name in NAMES:
        entries = declarations.get(name, [])
        if len(entries) != 1:
            errors.append(f"{name} {'missing' if not entries else 'declared more than once'}")
            for _, line in entries:
                print(line)
            continue
        kind, line = entries[0]
        print(line)
        if kind != "spin":
            errors.append(f"{name} declared as {kind}")

    if errors:
        for error in errors:
            print(f"{build} FAIL {error}")
    else:
        print(f"{build} PASS {len(NAMES)} spin options")
    return not errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("r15d", type=Path)
    parser.add_argument("kf", type=Path, metavar="kF")
    args = parser.parse_args()
    results = (audit("r15d", args.r15d), audit("kF", args.kf))
    raise SystemExit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
