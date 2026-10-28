"""Resolve git conflict blocks in the given files by union: ours, then theirs.

Usage: python union_conflicts.py [--blank] FILE [FILE...]
Only for files where both sides add independent lines (option lists, CMake targets, includes).
  --blank   insert one blank line between the two sides (declaration blocks in headers)
Rules: identical sides keep one copy; when both sides are only comment lines (a file header that each
branch worded differently), ours is kept. LF line ends are kept (bytes in, bytes out).
"""
import sys


def is_comment_block(block):
    return bool(block) and all(l.lstrip().startswith("//") for l in block)


def resolve(text, blank):
    out = []
    lines = text.split("\n")
    i = 0
    n = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("<<<<<<< "):
            ours, theirs = [], []
            i += 1
            while not lines[i].startswith("======="):
                ours.append(lines[i])
                i += 1
            i += 1
            while not lines[i].startswith(">>>>>>> "):
                theirs.append(lines[i])
                i += 1
            i += 1
            out.extend(ours)
            if theirs != ours and not (is_comment_block(ours) and is_comment_block(theirs)):
                if blank and ours and theirs and ours[-1].strip() and theirs[0].strip():
                    out.append("")
                out.extend(theirs)
            n += 1
            continue
        out.append(line)
        i += 1
    return "\n".join(out), n


args = sys.argv[1:]
blank = "--blank" in args
for path in [a for a in args if a != "--blank"]:
    with open(path, "rb") as f:
        data = f.read().decode("utf-8")
    new, n = resolve(data, blank)
    with open(path, "wb") as f:
        f.write(new.encode("utf-8"))
    print(f"{path}: {n} block(s) resolved by union")
