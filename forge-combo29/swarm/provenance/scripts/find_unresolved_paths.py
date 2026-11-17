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

    listing = subprocess.run(
        ["git", "rev-list", "--all", "--objects"],
        cwd=args.repo, capture_output=True, text=True, errors="replace",
    ).stdout.splitlines()
    pairs = []
    for line in listing:
        p = line.split(maxsplit=1)
        if len(p) == 2 and p[1].startswith("forge-combo29/swarm/"):
            pairs.append((p[0], p[1]))

    blobs = sorted({p[0] for p in pairs})
    texts = {}
    for s in range(0, len(blobs), 400):
        part = blobs[s : s + 400]
        out = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=args.repo,
            input="\n".join(part).encode(), capture_output=True,
        ).stdout
        i = 0
        while i < len(out):
            nl = out.index(b"\n", i)
            f = out[i:nl].decode().split()
            if len(f) < 3:
                i = nl + 1
                continue
            sha, size = f[0], int(f[2])
            data = out[nl + 1 : nl + 1 + size]
            i = nl + 1 + size + 1
            if b"\x00" not in data[:8192]:
                texts[sha] = data.decode("utf-8", errors="replace")

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
