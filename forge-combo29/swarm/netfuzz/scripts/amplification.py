#!/usr/bin/env python3
"""Memory amplification: allocated bytes per file byte, for accepted and refused files.

Two numbers matter and they are different:

  * the CLAIM amplification -- does a header claiming huge dimensions cause a huge
    allocation when the file is small? (the classic decompression-bomb shape)
  * the SLURP amplification -- does a large file cost memory before any check, even
    for a file that will certainly be refused?

The second is the one this loader has. It slurps to EOF into a vector first, so the
cost is bounded by the file's real length (unbounded for a pipe or /dev/zero) and the
header's claim is irrelevant to it.

Usage: amplification.py <probe> <pristine net> <manifest.json> <out.json> <workdir>
"""
import json
import os
import subprocess
import sys


def alloc(probe, path):
    proc = subprocess.run([probe, "loadalloc", path], capture_output=True, text=True, timeout=600)
    fields = {}
    for line in proc.stdout.splitlines():
        if line.startswith("ALLOC\t"):
            parts = line.split("\t")
            fields["verdict"] = parts[1]
            for part in parts[2:]:
                bits = part.split()
                if len(bits) == 2:
                    fields[bits[0]] = bits[1]
                elif bits:
                    fields["big"] = bits[1:]
            fields["detail"] = parts[-1]
    fields["rc"] = proc.returncode
    return fields


def main():
    probe, pristine, manifest_path, outpath, workdir = sys.argv[1:6]
    manifest = json.load(open(manifest_path))
    rows = []

    def row(label, path, note):
        info = alloc(probe, path)
        size = os.path.getsize(path) if os.path.isfile(path) else None
        total = int(info.get("total_bytes", 0))
        rec = {
            "label": label,
            "file_bytes": size,
            "verdict": info.get("verdict"),
            "total_alloc_bytes": total,
            "largest_alloc_bytes": int(info.get("largest", 0)),
            "peak_rss_kb": int(info.get("peak_rss_kb", 0) or 0),
            "big_allocs": info.get("big", []),
            "detail": info.get("detail", ""),
            "alloc_per_file_byte": (total / size) if size else None,
            "note": note,
        }
        rows.append(rec)
        print("%-34s %-8s file %10s alloc %11d ratio %s"
              % (label, rec["verdict"], size, total,
                 "n/a" if not rec["alloc_per_file_byte"] else "%.2fx" % rec["alloc_per_file_byte"]))

    row("pristine", pristine, "the real 6.3 MB net: the loader's true working set")
    for case in manifest["cases"]:
        if case["class"] in ("bomb", "control"):
            row(case["name"], os.path.join(manifest["outdir"], case["name"] + ".fnn3"), case["field"])

    valid = os.path.join(workdir, "valid_max.fnn3")
    if os.path.exists(valid):
        row("valid_max_dims", valid, "header and body agree at the format maximum")

    # Sparse files: real length large, cost on disk ~0. These answer "does a big file
    # cost memory even though it can only be refused?"
    for size_mb in (64, 512, 2048):
        path = os.path.join(workdir, "sparse_%dmb.fnn3" % size_mb)
        with open(path, "wb") as handle:
            handle.truncate(size_mb * 1024 * 1024)
        with open(path, "r+b") as handle:
            handle.write(b"FORGENN3")
        row("sparse_%dmb" % size_mb, path,
            "valid magic, wrong length: every byte is read before the length is checked")

    with open(outpath, "w") as handle:
        json.dump(rows, handle, indent=1)
    print("wrote", outpath)

    real = [r for r in rows if r["alloc_per_file_byte"]]
    print("\naccepted rows: %s" % ", ".join(r["label"] for r in rows if r["verdict"] == "ACCEPTED"))
    if real:
        print("alloc/file ratio: min %.2fx  max %.2fx"
              % (min(r["alloc_per_file_byte"] for r in real), max(r["alloc_per_file_byte"] for r in real)))


if __name__ == "__main__":
    main()
