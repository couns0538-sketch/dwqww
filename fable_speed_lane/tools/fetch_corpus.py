"""Download a text corpus from the blob-less clone for mechanism-level duplicate checks, without any checkout.

Reads the TSV written by tree_index.py, keeps the unique blobs whose path matches --include,
fetches them from origin in bulk (one promisor request per chunk), and writes each blob once to
OUT_DIR/<ext>/<sha>.<ext>. A manifest maps every blob back to a branch and path.
(Same tool as job 1's fable_search_gap/tools/fetch_corpus.py.)

usage: fetch_corpus.py REPO INDEX_TSV OUT_DIR --include REGEX [--exclude REGEX] [--max-bytes N]
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("repo")
    p.add_argument("index")
    p.add_argument("out_dir")
    p.add_argument("--include", required=True)
    p.add_argument("--exclude", default=None)
    p.add_argument("--max-bytes", type=int, default=2_000_000)
    a = p.parse_args()
    print(pinguard.ensure(), flush=True)
    inc = re.compile(a.include)
    exc = re.compile(a.exclude) if a.exclude else None
    blobs: dict[str, list] = {}
    with open(a.index, encoding="utf-8") as f:
        for line in f:
            sha, path, ref, n = line.rstrip("\n").split("\t")
            if not inc.search(path) or (exc and exc.search(path)):
                continue
            entry = blobs.setdefault(sha, [path, ref, 0, 0])
            entry[2] += 1
            entry[3] += int(n)
    shas = sorted(blobs)
    print(f"selected {len(shas)} unique blobs", flush=True)

    # Which ones are missing locally?
    check = subprocess.run(["git", "-C", a.repo, "cat-file", "--batch-check", "--batch-all-objects"],
                           capture_output=True, text=True, check=True).stdout
    have = {ln.split()[0] for ln in check.split("\n") if ln}
    missing = [s for s in shas if s not in have]
    print(f"already local {len(shas) - len(missing)}, to fetch {len(missing)}", flush=True)
    for i in range(0, len(missing), 800):
        chunk = missing[i:i + 800]
        r = subprocess.run(["git", "-C", a.repo, "-c", "fetch.negotiationAlgorithm=noop", "fetch", "origin",
                            "--no-tags", "--no-write-fetch-head", "--recurse-submodules=no",
                            "--filter=blob:none", "--stdin"],
                           input=("\n".join(chunk) + "\n").encode("ascii"), capture_output=True)  # bytes: no CRLF
        if r.returncode != 0:
            print(f"fetch chunk {i} failed: {r.stderr.decode('utf-8', 'replace')[-400:]}", flush=True)
            raise SystemExit(2)
        print(f"fetched {min(i + 800, len(missing))}/{len(missing)}", flush=True)

    os.makedirs(a.out_dir, exist_ok=True)
    written = skipped = total = 0
    with open(os.path.join(a.out_dir, "MANIFEST.tsv"), "a", encoding="utf-8", newline="\n") as man:
        for sha in shas:
            path, ref, n_paths, n_refs = blobs[sha]
            ext = os.path.splitext(path)[1].lstrip(".").lower() or "none"
            dst_dir = os.path.join(a.out_dir, ext)
            dst = os.path.join(dst_dir, f"{sha}.{ext}")
            if os.path.exists(dst):
                continue
            size = int(subprocess.run(["git", "-C", a.repo, "cat-file", "-s", sha], capture_output=True,
                                      text=True, check=True).stdout)
            if size > a.max_bytes:
                skipped += 1
                man.write(f"{sha}\t{size}\tSKIPPED_TOO_BIG\t{ref}\t{path}\t{n_paths}\t{n_refs}\n")
                continue
            data = subprocess.run(["git", "-C", a.repo, "cat-file", "blob", sha], capture_output=True,
                                  check=True).stdout
            os.makedirs(dst_dir, exist_ok=True)
            with open(dst, "wb") as out:
                out.write(data)
            man.write(f"{sha}\t{size}\t{ext}/{sha}.{ext}\t{ref}\t{path}\t{n_paths}\t{n_refs}\n")
            written += 1
            total += size
    print(f"written {written} files, {total / 1e6:.1f} MB, skipped {skipped} (too big)", flush=True)


if __name__ == "__main__":
    main()
