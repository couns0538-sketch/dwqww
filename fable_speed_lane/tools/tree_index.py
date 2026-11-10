"""Index every file path of every fetched remote branch (trees only, no file contents are downloaded).

Output TSV columns: blob_sha, path, first_ref, ref_count
Used for the duplicate check: find notes, patches, candidate lists and source snapshots on all
branches without checking any of them out. (Same tool as job 1's fable_search_gap/tools/tree_index.py.)

usage: tree_index.py REPO OUT_TSV
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, "-c", "core.quotepath=false", *args], check=True,
                          capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def main():
    repo, out = sys.argv[1], sys.argv[2]
    print(pinguard.ensure(), flush=True)
    refs = [r for r in git(repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").split("\n")
            if r and r not in ("origin/HEAD", "origin")]
    seen: dict[tuple[str, str], list] = {}
    tips = {}
    for i, ref in enumerate(refs, 1):
        tips[ref] = git(repo, "rev-parse", ref).strip()
        for line in git(repo, "ls-tree", "-r", ref).split("\n"):
            if "\t" not in line:
                continue
            meta, path = line.split("\t", 1)
            sha = meta.split()[2]
            key = (sha, path)
            if key in seen:
                seen[key][1] += 1
            else:
                seen[key] = [ref, 1]
        if i % 50 == 0:
            print(f"{i}/{len(refs)} refs, {len(seen)} unique (blob, path)", flush=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for (sha, path), (ref, n) in sorted(seen.items(), key=lambda kv: kv[0][1]):
            f.write(f"{sha}\t{path}\t{ref}\t{n}\n")
    with open(out + ".tips", "w", encoding="utf-8", newline="\n") as f:
        for ref in refs:
            f.write(f"{tips[ref]}\t{ref}\n")
    print(f"refs={len(refs)} unique(blob,path)={len(seen)} -> {out}", flush=True)


if __name__ == "__main__":
    main()
