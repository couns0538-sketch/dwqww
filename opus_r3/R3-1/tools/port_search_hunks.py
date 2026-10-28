#!/usr/bin/env python3
"""Port a branch's src/search.cpp hunks (written against the AL1 s198 single-file search.cpp) onto the O3
module layout (src/search.cpp + src/search/*.inc|*.hpp).

usage: port_search_hunks.py <diff-file> [--apply]   (run from the stack worktree)
  <diff-file>: `git diff d4f4312 <branch> -- src/search.cpp`
For every hunk, the "old" side (context + removed lines) is searched verbatim in each module file. A hunk whose
old side occurs exactly once in exactly one file is rewritten for that file and, with --apply, applied with
GNU patch -F0 (exact context, any offset). Every other hunk is printed in full for porting by hand.
Exit status 0 when every hunk was placed.
"""
import glob
import os
import subprocess
import sys

PATCH = "C:/Program Files/Git/usr/bin/patch.exe"


def hunks(diff_text):
    lines = diff_text.split("\n")
    out, cur = [], None
    for l in lines:
        if l.startswith("@@"):
            if cur:
                out.append(cur)
            cur = [l]
        elif cur is not None:
            if l.startswith((" ", "+", "-")) or l == "" or l.startswith("\\"):
                cur.append(l)
    if cur:
        out.append(cur)
    # drop trailing empty lines that are not part of the hunk
    res = []
    for h in out:
        while h and h[-1] == "":
            h.pop()
        res.append(h)
    return res


def old_side(h):
    return [l[1:] for l in h[1:] if l.startswith((" ", "-"))]


def main():
    diff_text = open(sys.argv[1], "rb").read().decode("utf-8")
    apply = "--apply" in sys.argv
    files = ["src/search.cpp"] + sorted(glob.glob("src/search/*.inc") + glob.glob("src/search/*.hpp"))
    texts = {f: open(f, "rb").read().decode("utf-8").split("\n") for f in files}
    ok = True
    for k, h in enumerate(hunks(diff_text)):
        old = old_side(h)
        found = []
        for f, t in texts.items():
            n = sum(1 for i in range(len(t) - len(old) + 1) if t[i:i + len(old)] == old)
            if n:
                found.append((f, n))
        if len(found) == 1 and found[0][1] == 1:
            target = found[0][0].replace("\\", "/")
            print(f"hunk {k + 1}: {h[0][:40]} -> {target}")
            if apply:
                body = "\n".join(h) + "\n"
                patch = f"--- a/{target}\n+++ b/{target}\n" + body
                r = subprocess.run([PATCH, "-p1", "-F0", "--no-backup-if-mismatch"], input=patch.encode("utf-8"),
                                   capture_output=True)
                print("   ", r.stdout.decode().strip().replace("\n", " | "), r.stderr.decode().strip())
                if r.returncode != 0:
                    ok = False
                texts[found[0][0]] = open(found[0][0], "rb").read().decode("utf-8").split("\n")
        else:
            ok = False
            print(f"hunk {k + 1}: NOT PLACED (matches: {found})")
            print("\n".join("      " + l for l in h))
    sys.exit(0 if ok else 1)


main()
