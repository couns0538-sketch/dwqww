#!/usr/bin/env python3
"""Find every swarm path whose contents carry an unresolvable build hash.

This produces ``evidence/unresolved_hash_paths.json``, which ``transitive_deps.py``
consumes. It exists as its own script rather than a one-off shell command because a
provenance audit that depended on an unrecorded command would be committing the very
defect it is auditing.

Output: { "<hash>": ["forge-combo29/swarm/NN/...", ...] }
"""
import argparse
import collections
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pathsafe

# The hashes with no recorded rebuild recipe. Kept here as the single source of truth
# for this step; the verdicts that justify the list live in evidence/build_verdicts.json.
UNRESOLVED = [
    "b109a0a5",
    "7c4e1aee",
    "6e0e9522",
    "81c52608",
    "1a9460d6",
    "0dceb07e",
    "571e7c83",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/agent/repos/dwqww")
    ap.add_argument("--out", default="evidence")
    args = ap.parse_args()

    # Exclude this audit's own directory. Its evidence files quote the very hashes
    # being searched for, so including them made the map count the audit as another
    # place the hash occurs -- 8-10 self-referential paths per hash, growing with
    # every re-run. A census that counts itself is not a census.
    pairs = [
        (b, p)
        for b, p in pathsafe.swarm_objects(args.repo)
        if "/swarm/provenance/" not in p
    ]
    texts = pathsafe.read_text_blobs(args.repo, [b for b, _ in pairs])

    hits = collections.defaultdict(set)
    for blob, path in pairs:
        t = texts.get(blob)
        if not t:
            continue
        for h in UNRESOLVED:
            if h in t:
                hits[h].add(path)

    out_path = pathsafe.checked_path(args.out, os.getcwd(), create=True)
    pathsafe.dump_json({k: sorted(v) for k, v in hits.items()}, "unresolved_hash_paths.json", out_path)
    for h in UNRESOLVED:
        print(f"{h}: {len(hits[h])} paths")


if __name__ == "__main__":
    main()
