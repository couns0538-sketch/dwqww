#!/usr/bin/env python3
"""S10-4 / S10-5: delivery hygiene check (read-only).

Reports for a folder (--dir) or a git tree (--git REPO --tree COMMIT [--prefix P ...]):
  * `_before_` copies (S10-4: a delivery keeps the finals plus one diff log, never `_before_<fix>` copies),
  * groups of byte-identical files stored under several paths (duplicate copies),
  * every .tar.gz with its size in bytes (S10-5: list every .tar.gz size).
Nothing is changed or deleted. Exit 1 if any `_before_` copy is found (use it as a gate on our own deliverables).
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

BEFORE = "_before_"


def scan_dir(root):
    rows = []
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            rows.append({"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size,
                         "id": hashlib.sha256(p.read_bytes()).hexdigest()})
    return rows


def scan_git(repo, tree, prefixes):
    out = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-l", tree, "--", *prefixes], capture_output=True,
                         text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, blob, size = meta.split()
        if kind == "blob":
            rows.append({"path": path, "bytes": int(size), "id": blob})
    return rows


def check(rows):
    before = [r["path"] for r in rows if BEFORE in Path(r["path"]).name]
    groups = {}
    for r in rows:
        groups.setdefault(r["id"], []).append(r)
    dups = [{"bytes": g[0]["bytes"], "paths": [r["path"] for r in g]} for g in groups.values() if len(g) > 1 and g[0]["bytes"] > 0]
    dups.sort(key=lambda d: (-d["bytes"] * (len(d["paths"]) - 1), d["paths"][0]))
    tgz = [{"path": r["path"], "bytes": r["bytes"]} for r in rows if r["path"].endswith(".tar.gz")]
    return {"files": len(rows), "bytes": sum(r["bytes"] for r in rows), "before_copies": before,
            "duplicate_groups": dups, "duplicate_extra_bytes": sum(d["bytes"] * (len(d["paths"]) - 1) for d in dups),
            "tar_gz": tgz, "tar_gz_total_bytes": sum(t["bytes"] for t in tgz)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir")
    ap.add_argument("--git")
    ap.add_argument("--tree")
    ap.add_argument("--prefix", action="append", default=[])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    if bool(a.dir) == bool(a.git):
        ap.error("give exactly one of --dir or --git/--tree")
    rows = scan_dir(a.dir) if a.dir else scan_git(a.git, a.tree, a.prefix)
    rep = check(rows)
    print(f"files {rep['files']}, bytes {rep['bytes']:,}")
    print(f"_before_ copies: {len(rep['before_copies'])}" + "".join(f"\n  {p}" for p in rep["before_copies"]))
    print(f"duplicate groups: {len(rep['duplicate_groups'])} (extra bytes {rep['duplicate_extra_bytes']:,})")
    for d in rep["duplicate_groups"]:
        print(f"  {d['bytes']:>10,} x{len(d['paths'])}: " + " | ".join(d["paths"]))
    print(f".tar.gz files: {len(rep['tar_gz'])} (total {rep['tar_gz_total_bytes']:,} bytes)")
    for t in rep["tar_gz"]:
        print(f"  {t['bytes']:>12,}  {t['path']}")
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 1 if rep["before_copies"] else 0


if __name__ == "__main__":
    sys.exit(main())
