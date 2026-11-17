#!/usr/bin/env python3
"""Transitive dependency: which FINDINGS rest, by their own evidence path, on an
unresolvable build hash.

A finding row names a script or a raw output file as the thing that shows it again.
If that file's own contents carry a binary sha256 that cannot be rebuilt, the finding
inherits the gap even though the finding row never typed the hash itself. This is the
step that stops the audit from reporting "only 31 findings are affected" when the
real number is larger -- the first pass made exactly that mistake, because it only
looked at hashes typed in the row.

Output: evidence/transitive_deps.json
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathsafe

UNRESOLVED_HASHES = {
    "b109a0a5": "base ASan/UBSan build (no recipe recorded)",
    "7c4e1aee": "an unrecorded variant of the base tree (no recipe recorded)",
    "6e0e9522": "seat 12 build (no recipe recorded)",
    "81c52608": "seat 01 'mine' build (no recipe recorded)",
    "1a9460d6": "seat 28 planted control (no recipe recorded)",
    "0dceb07e": "seat 28 planted control (no recipe recorded)",
    "571e7c83": "seat 27 SAN build (no recipe recorded)",
}

# a path or command mentioned inside a finding row
PATH_RE = re.compile(r"forge-combo29/swarm/\d+/[A-Za-z0-9_./-]+")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="evidence/finding_rows.json")
    ap.add_argument(
        "--hits",
        default="evidence/unresolved_hash_paths.json",
        help="hash -> swarm paths map (default: this audit's own evidence file)",
    )
    ap.add_argument("--out", default="evidence/transitive_deps.json")
    args = ap.parse_args()

    rows = pathsafe.load_json(args.rows, os.getcwd())
    hits = pathsafe.load_json(args.hits, os.getcwd())

    # hash -> set of directories it appears under, so a row naming a sibling file counts
    hash_dirs = collections.defaultdict(set)
    hash_files = collections.defaultdict(set)
    for h, paths in hits.items():
        for p in paths:
            hash_files[h].add(p)
            hash_dirs[h].add(os.path.dirname(p))

    # A finding depends transitively only if a file it NAMES actually contains the
    # hash. An earlier version matched on shared parent directory, which produced six
    # false positives from seat 30: its rows cite read_board.sh (a harness that lists
    # other seats' findings) and the hash lived in a *sibling* raw file. Requiring the
    # literal hash inside the named file is stricter and is the claim we want.
    out = []
    for r in rows:
        named = set(PATH_RE.findall(r["row_excerpt"]))
        for h in UNRESOLVED_HASHES:
            direct = any(h in b for b in r["build_refs"])
            carried = sorted(n for n in named if n in hash_files[h])
            if direct or carried:
                out.append(
                    {
                        "seat": r["seat"],
                        "finding": r["finding"],
                        "hash": h,
                        "hash_note": UNRESOLVED_HASHES[h],
                        "via": "typed in the row" if direct else "a file the row names contains it",
                        "evidence_named": carried[:4] or sorted(named)[:4],
                    }
                )

    pathsafe.dump_json(out, args.out, os.getcwd())
    byh = collections.Counter(o["hash"] for o in out)
    fnd = {(o["seat"], o["finding"]) for o in out}
    print(f"findings transitively dependent on an unresolvable build hash: {len(fnd)}")
    for h, n in byh.most_common():
        seats = sorted({o["seat"] for o in out if o["hash"] == h})
        print(f"  {h}  findings={n:3d} seats={seats[:8]}")


if __name__ == "__main__":
    main()
