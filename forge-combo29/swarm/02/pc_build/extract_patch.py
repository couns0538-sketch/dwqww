#!/usr/bin/env python3
"""S02: extract the r15 patch from FABLE_TO_swarm_5.md exactly, and check its sha256.

File 5 says: "sha256 of the patch text (from its first `diff` line to its last line, as saved below) starts with
d6bd72c531f785f4". So the text to hash starts at the first line beginning `diff ` and ends at the last line of
the fenced block. I reproduce that slice exactly and compare, and I FAIL LOUDLY if it does not match rather than
building an unverified patch.

usage: extract_patch.py <FABLE_TO_swarm_5.md path> <outdir>
"""
import hashlib
import os
import subprocess
import sys

src = sys.argv[1]
outdir = sys.argv[2]
EXPECT_PREFIX = "d6bd72c531f785f4"

text = open(src, encoding="utf-8").read()
lines = text.splitlines(keepends=True)

# the fenced block that holds the patch is the one after "## The patch"
start_fence = None
for i, line in enumerate(lines):
    if line.strip() == "## The patch":
        for j in range(i + 1, len(lines)):
            if lines[j].lstrip().startswith("```"):
                start_fence = j
                break
        break
if start_fence is None:
    sys.exit("FAIL: no '## The patch' section found")

end_fence = None
for j in range(start_fence + 1, len(lines)):
    if lines[j].lstrip().startswith("```"):
        end_fence = j
        break
if end_fence is None:
    sys.exit("FAIL: the patch fence is not closed")

body = lines[start_fence + 1:end_fence]
# the hash covers the text from the first `diff ` line to the last line of the block
first = next(i for i, l in enumerate(body) if l.startswith("diff "))
patch_text = "".join(body[first:])
# trim any trailing blank lines so the slice is exactly "the last line"
patch_text = patch_text.rstrip("\n") + "\n"

os.makedirs(outdir, exist_ok=True)
path = os.path.join(outdir, "pc_r15.patch")
with open(path, "w", encoding="utf-8", newline="") as fh:
    fh.write(patch_text)

digest = hashlib.sha256(patch_text.encode()).hexdigest()
print("patch written to %s" % path)
print("lines %d" % patch_text.count("\n"))
print("sha256 %s" % digest)
print("file 5 states it should start with %s" % EXPECT_PREFIX)
if not digest.startswith(EXPECT_PREFIX):
    sys.exit("FAIL: the extracted patch's sha256 does not match file 5's stated prefix. NOT BUILDING IT.")
print("PASS: patch sha256 matches file 5's stated prefix")

# also record what the patch touches, from the patch itself
files = sorted({l.split()[2][2:] for l in patch_text.splitlines()
                if l.startswith("--- a/")})
print("files touched (%d):" % len(files))
for f in files:
    print("  %s" % f)
open(os.path.join(outdir, "patch_files.txt"), "w").write("\n".join(files) + "\n")
open(os.path.join(outdir, "patch_sha256.txt"), "w").write(
    "extracted %s\nsha256 %s\nfile5_stated_prefix %s\nlines %d\n" %
    (path, digest, EXPECT_PREFIX, patch_text.count("\n")))
