#!/usr/bin/env python3
"""Apply the unified-diff hunks for ONE file of a patch to a base file and check the result's md5 (read-only inputs).
Used for S09-5 to rebuild Coder's trained 8-head net (fc_buckets8_b8ep8_h256e12, md5 09227945...) from the lock
archive's research patch and the h256_e12 net (md5 6d22f612...), instead of copying from the training folder.
usage: opus_s09_patch_one_file.py PATCH TARGET_SUFFIX BASE OUT --md5 EXPECTED
Exit 0 only if every hunk's context/removed lines match exactly and the output md5 equals --md5."""
from __future__ import annotations
import argparse, hashlib, re, sys
from pathlib import Path

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def file_hunks(patch_lines, suffix):
    """Return the hunks of the section whose +++ path ends with suffix (counts drive the parse, not prefixes)."""
    inside, hunks, old_left, new_left = False, [], 0, 0
    for line in patch_lines:
        if old_left > 0 or new_left > 0:  # inside a hunk body
            tag = line[:1]
            if tag == "\\":
                continue
            hunks[-1]["lines"].append(line)
            if tag in (" ", "-"):
                old_left -= 1
            if tag in (" ", "+"):
                new_left -= 1
            continue
        if line.startswith("--- "):
            continue
        if line.startswith("+++ "):
            inside = line[4:].split("\t")[0].strip().endswith(suffix)
            continue
        m = HUNK.match(line)
        if m and inside:
            old_left, new_left = int(m[2] or 1), int(m[4] or 1)
            hunks.append({"old_start": int(m[1]), "lines": []})
        elif m:
            old_left, new_left = int(m[2] or 1), int(m[4] or 1)
            hunks.append({"old_start": -1, "lines": [], "skip": True})
    return [h for h in hunks if not h.get("skip")]


def apply(base_lines, hunks):
    out, pos = [], 0
    for h in hunks:
        start = h["old_start"] - 1
        out.extend(base_lines[pos:start])
        pos = start
        for line in h["lines"]:
            tag, text = line[:1], line[1:]
            if tag in (" ", "-"):
                if base_lines[pos] != text:
                    raise ValueError(f"mismatch at base line {pos + 1}")
                pos += 1
                if tag == " ":
                    out.append(text)
            elif tag == "+":
                out.append(text)
    out.extend(base_lines[pos:])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("patch")
    ap.add_argument("suffix")
    ap.add_argument("base")
    ap.add_argument("out")
    ap.add_argument("--md5", required=True)
    a = ap.parse_args(argv)
    patch_lines = Path(a.patch).read_text(encoding="utf-8").split("\n")
    hunks = file_hunks(patch_lines, a.suffix)
    base = Path(a.base).read_bytes().decode("utf-8")
    trailing = base.endswith("\n")
    lines = apply(base.split("\n")[:-1] if trailing else base.split("\n"), hunks)
    data = ("\n".join(lines) + ("\n" if trailing else "")).encode("utf-8")
    md5 = hashlib.md5(data).hexdigest()
    print(f"{len(hunks)} hunks applied; out {len(data)} bytes md5 {md5} sha256 {hashlib.sha256(data).hexdigest()}")
    if md5 != a.md5:
        print(f"MD5 MISMATCH: expected {a.md5}")
        return 1
    if Path(a.out).exists():
        raise SystemExit(f"{a.out} exists")
    Path(a.out).write_bytes(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
