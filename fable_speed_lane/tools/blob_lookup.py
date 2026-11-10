"""blob_lookup.py - is the lock's source on any fetched branch? Looks every snapshot file up by git blob id.

For each file of the source snapshot the git blob id is computed locally (sha1 of "blob <size>\\0" + bytes,
the id git itself gives the file) and looked up in the tree index of all fetched branches
(tools/tree_index.py: blob_sha, path, first_ref, ref_count). A file whose id is in no branch tree exists on
no fetched branch in that exact form. Output TSV: path, blob id, branches holding that blob, one example ref.

usage: blob_lookup.py SNAPSHOT_DIR TREE_INDEX_TSV OUT_TSV
"""
import hashlib
import os
import sys


def blob_id(path):
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main():
    snap, index, out = sys.argv[1], sys.argv[2], sys.argv[3]
    seen = {}
    refs_total = set()
    with open(index, encoding="utf-8", errors="replace") as f:
        next(f, None)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 4:
                n, first = seen.get(p[0], (0, p[2]))
                seen[p[0]] = (max(n, int(p[3]) if p[3].isdigit() else 0), first)
                refs_total.add(p[2])
    rows = []
    for sub in ("include", "src"):
        for d, _dirs, files in os.walk(os.path.join(snap, sub)):
            for name in sorted(files):
                path = os.path.join(d, name)
                rel = os.path.relpath(path, snap).replace("\\", "/")
                b = blob_id(path)
                n, first = seen.get(b, (0, ""))
                rows.append((rel, b, n, first))
    rows.sort()
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("path\tgit_blob_id\tbranches_holding_this_blob\texample_ref\n")
        for r in rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")
    absent = [r[0] for r in rows if r[2] == 0]
    print(f"{len(rows)} snapshot files, {len(seen)} distinct blobs in the index; "
          f"{len(absent)} snapshot files are on no fetched branch: {', '.join(absent) if absent else '-'}")


if __name__ == "__main__":
    main()
