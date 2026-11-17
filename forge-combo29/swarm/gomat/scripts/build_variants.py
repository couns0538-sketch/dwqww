#!/usr/bin/env python3
"""Build every ablation variant and REFUSE a table in which any binary matches
the control build's hash.

The first version of this build loop reported thirteen "successes" whose
binaries were byte-identical to the control — the -D definitions never reached
the compiler. Thirteen identical binaries is not a null result, it is one build
copied thirteen times, and it would have produced a perfectly clean table
saying "no heuristic gates mate mode". This script makes that outcome
impossible: the control hash is read first and any collision is a hard error.

Usage: build_variants.py [--dir /tmp/ab] [--jobs 4]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from variants import GATES  # noqa: E402

# Every single gate is its own arm, so the "two at a time" question in the
# assignment can be answered both alone and in pairs.
SINGLES = list(GATES)
PAIRS = [
    ("TTq", "TTmain"),
    ("RazorRfpNull", "Iir"),
    ("SingularExt", "CheckExt"),
    ("Lmr", "FutilityPrune"),
    ("QuietExtinction", "QSearchPrune"),
    ("Window", "Lmr"),
]
SENTINELS = {
    "ALL": list(GATES),
    # The pair the mechanism most plausibly needs: if the window narrows AND the
    # TT may cut, mate mode should behave like an ordinary search.
    "TT_BOTH": ["TTq", "TTmain"],
}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(root: str, out: str, gates: list[str], jobs: int) -> str:
    subprocess.run([sys.executable, os.path.join(HERE, "variants.py"),
                    "--src", root, "--out", out, "--gates", ",".join(gates)],
                   check=True, capture_output=True)
    subprocess.run(["cmake", "-S", out, "-B", os.path.join(out, "build"), "-G", "Ninja",
                    "-DCMAKE_BUILD_TYPE=Release",
                    "-DCMAKE_CXX_COMPILER=/usr/bin/g++"],
                   check=True, capture_output=True)
    env = dict(os.environ, LIBRARY_PATH="/usr/lib/gcc/x86_64-linux-gnu/13")
    subprocess.run(["cmake", "--build", os.path.join(out, "build"), "-j", str(jobs)],
                   check=True, capture_output=True, env=env)
    return sha256(os.path.join(out, "build", "forge"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dir", default="/tmp/ab")
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args()

    arms: list[tuple[str, list[str]]] = [("control", [])]
    arms += [(g, [g]) for g in SINGLES]
    arms += [(f"{a}+{b}", [a, b]) for a, b in PAIRS]
    arms += [(name, gates) for name, gates in SENTINELS.items()]

    seen: dict[str, tuple[str, frozenset]] = {}
    table = []
    for name, gates in arms:
        out = os.path.join(args.dir, name)
        digest = build(args.root, out, gates, args.jobs)
        table.append((name, gates, digest))
        print(f"{name:24s} {'+'.join(gates) or '(pure mate mode)':60s} {digest[:16]}", flush=True)
        key = frozenset(gates)
        if digest in seen:
            other_name, other_key = seen[digest]
            if other_key == key:
                # Same gate set under two names: an alias, not a broken arm.
                print(f"    (alias of {other_name}: same gate set)")
                continue
            print(f"\nFAIL: {name} {sorted(key)} is BYTE-IDENTICAL to {other_name} "
                  f"{sorted(other_key)}, but those are DIFFERENT gate sets.")
            print("The gate definitions did not reach the compiler, so this is not an "
                  "ablation arm and any 'no effect' it reports would be an artefact.")
            return 1
        seen[digest] = (name, key)

    distinct_sets = len({frozenset(g) for _, g, _ in table})
    distinct_bins = len({d for _, _, d in table})
    print(f"\n{len(table)} arms, {distinct_sets} distinct gate sets, "
          f"{distinct_bins} distinct binaries; control {table[0][2][:16]}")
    if distinct_sets != distinct_bins:
        print("FAIL: two different gate sets share a binary; the ablation is not binding.")
        return 1
    with open(os.path.join(args.dir, "BUILDS.txt"), "w") as fh:
        fh.write("name\tgates\tsha256\n")
        for name, gates, digest in table:
            fh.write(f"{name}\t{'+'.join(gates) or 'CONTROL'}\t{digest}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
