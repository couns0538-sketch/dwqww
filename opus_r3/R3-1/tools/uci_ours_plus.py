"""Resolve src/uci.cpp merge conflicts as "ours", then re-insert the merged branch's added-line runs.

usage: python uci_ours_plus.py <branch-ref>      (run from the stack worktree during a merge)
Each '+' run of `git diff <merge-base> <branch> -- src/uci.cpp` is inserted before the context line that follows
it (the anchor, which must occur exactly once in the resolved file) unless the run is already present verbatim.
A shared comment line ("Search options added after AL1 s198 ...") already present is not inserted twice.
Prints every '+' line of the branch diff that is missing from the result (should be none).
"""
import subprocess
import sys

branch = sys.argv[1]
path = "src/uci.cpp"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout.decode("utf-8")


def resolve_ours(text):
    lines = text.split("\n")
    out, i, n = [], 0, 0
    while i < len(lines):
        if lines[i].startswith("<<<<<<< "):
            i += 1
            while not lines[i].startswith("======="):
                out.append(lines[i]); i += 1
            while not lines[i].startswith(">>>>>>> "):
                i += 1
            i += 1; n += 1
            continue
        out.append(lines[i]); i += 1
    return out, n


lines, n = resolve_ours(open(path, "rb").read().decode("utf-8"))
print("conflict blocks resolved as ours:", n)
base = git("merge-base", "HEAD", branch).strip()
diff = git("diff", base, branch, "--", path).split("\n")
runs, cur, in_hunk = [], [], False
for raw in diff:
    if raw.startswith("@@"):
        in_hunk = True
        continue
    if not in_hunk or raw.startswith("\\"):
        continue
    if raw.startswith("+"):
        cur.append(raw[1:])
    elif raw.startswith("-"):
        if cur:
            runs.append((cur, None)); cur = []
    else:
        if cur:
            runs.append((cur, raw[1:] if raw else "")); cur = []


def contains_run(hay, run):
    k = len(run)
    return any(hay[i:i + k] == run for i in range(len(hay) - k + 1))


for run, anchor in runs:
    if contains_run(lines, run):
        continue
    run = [l for l in run if not ("Search options added after AL1 s198" in l and l in lines)]
    if not run or contains_run(lines, run):
        continue
    if anchor is None:
        print("RUN WITHOUT ANCHOR (resolve by hand):", run[:2]); continue
    hits = [i for i, l in enumerate(lines) if l == anchor]
    if len(hits) != 1:
        print("ANCHOR NOT UNIQUE (%d) for run %r -> anchor %r" % (len(hits), run[:1], anchor)); continue
    lines[hits[0]:hits[0]] = run
    print("inserted %d line(s) before %r" % (len(run), anchor.strip()[:60]))
open(path, "wb").write("\n".join(lines).encode("utf-8"))
added = [l[1:] for l in diff if l.startswith("+") and not l.startswith("+++")]
missing = [l for l in added if l not in lines]
print("branch '+' lines missing from the result:", len(missing))
for l in missing[:20]:
    print("   ", l)
