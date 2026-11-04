#!/usr/bin/env python3
"""hash_sweep.py - Opus R14-B: do the hashes the documents cite still match something real? (own code, stdlib only)

usage: python -I -B hash_sweep.py --docs DOC... --files PATH... [--repo REPO] [--allow FILE]
Every hex token of 8-64 characters with at least one letter a-f in the documents must be a prefix of the sha256 or
md5 of one of the files given (directories are walked), or of a commit in REPO (`git rev-list --all`), or be listed in
the allow file (one token per line, then a reason: historical versions and external references that were checked by
hand). Tokens that match nothing are printed with file:line; exit 1 if there is any, else 0.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys

TOKEN = re.compile(r"(?<![0-9A-Za-z])([0-9a-f]{8,64})(?![0-9A-Za-z])")


def digests(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            sha.update(block)
            md5.update(block)
    return sha.hexdigest(), md5.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--allow")
    a = ap.parse_args()
    # final bug hunt (04:15): a missing doc / allow file / repo was a traceback, and a misspelt --files path hashed
    # nothing, so every cited hash looked unmatched (exit 1, as if the documents were wrong)
    problems = [f"--docs {d}: not a file" for d in a.docs if not os.path.isfile(d)]
    problems += [f"--files {f}: not found" for f in a.files if not os.path.exists(f)]
    if a.allow and not os.path.isfile(a.allow):
        problems.append(f"--allow {a.allow}: not a file")
    if problems:
        print("hash_sweep: " + "\nhash_sweep: ".join(problems), file=sys.stderr)
        return 2
    allowed = {}
    if a.allow:
        with open(a.allow, encoding="utf-8") as fh:
            for line in fh:
                if line.strip() and not line.startswith("#"):
                    tok, _, why = line.strip().partition(" ")
                    allowed[tok] = why.strip()
    known = {}  # full hex digest -> description
    for root in a.files:
        paths = [root] if os.path.isfile(root) else [os.path.join(d, f) for d, _, fs in os.walk(root) for f in fs
                                                      if "/.git" not in d.replace("\\", "/")]
        for p in paths:
            try:
                s, m = digests(p)
            except OSError:
                continue
            known.setdefault(s, f"sha256 {p}")
            known.setdefault(m, f"md5 {p}")
    commits = []
    if a.repo:
        out = subprocess.run(["git", "-C", a.repo, "rev-list", "--all"], capture_output=True, text=True)
        if out.returncode:
            print(f"hash_sweep: --repo {a.repo}: git rev-list failed: {out.stderr.strip()[:200]}", file=sys.stderr)
            return 2
        commits = out.stdout.split()
    print(f"{len(known) // 2} files hashed, {len(commits)} commits")
    unmatched, kinds = [], {"file": 0, "commit": 0, "allowed": 0}
    for doc in a.docs:
        with open(doc, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                for tok in TOKEN.findall(line):
                    if not re.search("[a-f]", tok):
                        continue
                    if any(h.startswith(tok) for h in known):
                        kinds["file"] += 1
                    elif any(c.startswith(tok) for c in commits):
                        kinds["commit"] += 1
                    elif any(tok.startswith(t) or t.startswith(tok) for t in allowed):
                        kinds["allowed"] += 1
                    else:
                        unmatched.append(f"{doc}:{n}: {tok}")
    print(f"tokens matching a file hash: {kinds['file']}, a commit: {kinds['commit']}, the allow list: "
          f"{kinds['allowed']}, nothing: {len(unmatched)}")
    for u in unmatched:
        print("  " + u)
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
