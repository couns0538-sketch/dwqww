"""Build one fix commit per affected branch in the bare repository copy. Nothing is pushed and no ref is moved here.

usage: python -I make_fix_commits.py <bare repo> <fix scripts dir> <out.tsv> <author name> <author email> [--build]

For every refs/heads/* branch (lock/* and main are never touched):
  - opus_round1/C4/instrument_refresh_stats.py is removed when it is the known blob;
  - the three tablebase download scripts are replaced by the repaired files when they are the known original blobs.
Without --build it only prints the plan. With --build it writes the new blobs, trees and commit objects (each commit
has the branch tip as its only parent) and one line per branch to <out.tsv>: branch, old tip, new commit, changes.
A path whose blob differs from the known one is reported and left alone.
"""
import os
import subprocess
import sys

repo, fixdir, out_path, author_name, author_email = sys.argv[1:6]
build = "--build" in sys.argv[6:]
env = dict(os.environ, GIT_NO_LAZY_FETCH="1",
           GIT_AUTHOR_NAME=author_name, GIT_AUTHOR_EMAIL=author_email,
           GIT_COMMITTER_NAME=author_name, GIT_COMMITTER_EMAIL=author_email)

REMOVE = {"opus_round1/C4/instrument_refresh_stats.py": "8f7e7f7fd7eabe98babd9d29b00987cbfb81d6bd"}
REPLACE = {
    "opus_round1/C1/ci_fetch_tables.sh": ("71e2fc45324c394097a8b96aafada7f410072e60", "C1_ci_fetch_tables.sh"),
    "opus_round1/C1/download_tb.sh": ("18c5c0ffae5953beded3b032362e2c8c23ed22dd", "C1_download_tb.sh"),
    "opus_r13/p6/ci_fetch_tables.sh": ("6a55e3a3e6898155bcb528dc08220c7846d597b7", "p6_ci_fetch_tables.sh"),
}
NEVER = ("lock/", "main")


def git(*args, data=None):
    p = subprocess.run(["git", "--git-dir", repo, *args], input=data, capture_output=True, env=env)
    if p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {p.stderr.decode('utf-8', 'replace')}")
    return p.stdout


def ls(tree):
    out = []
    for rec in git("ls-tree", "-z", tree).split(b"\0"):
        if rec:
            meta, name = rec.split(b"\t", 1)
            mode, kind, oid = meta.split()
            out.append([mode, kind, oid, name])
    return out


def mktree(entries):
    data = b"".join(m + b" " + k + b" " + o + b"\t" + n + b"\0" for m, k, o, n in entries)
    return git("mktree", "-z", "--missing", data=data).strip()


def blob_at(tip, path):
    p = subprocess.run(["git", "--git-dir", repo, "rev-parse", "--verify", "--quiet", f"{tip}:{path}"],
                       capture_output=True, env=env)
    return p.stdout.decode().strip() if p.returncode == 0 else None


def edit(tree, parts, new_oid):
    """Return the oid of `tree` with the file at `parts` removed (new_oid None) or replaced; None if it gets empty."""
    entries = ls(tree)
    name = parts[0].encode()
    for i, e in enumerate(entries):
        if e[3] == name:
            break
    else:
        raise SystemExit(f"path component {parts[0]} not found")
    if len(parts) == 1:
        if new_oid is None:
            del entries[i]
        else:
            entries[i][2] = new_oid.encode()
    else:
        sub = edit(entries[i][2].decode(), parts[1:], new_oid)
        if sub is None:
            del entries[i]
        else:
            entries[i][2] = sub
    return mktree(entries) if entries else None


new_blob = {}
if build:
    for path, (_, fname) in REPLACE.items():
        new_blob[path] = git("hash-object", "-w", "--no-filters", os.path.join(fixdir, fname)).decode().strip()
else:
    for path, (_, fname) in REPLACE.items():
        new_blob[path] = git("hash-object", "--no-filters", os.path.join(fixdir, fname)).decode().strip()

refs = [l.split() for l in git("for-each-ref", "--format=%(objectname) %(refname)", "refs/heads").decode().splitlines()]
rows, skipped = [], []
for tip, ref in refs:
    branch = ref[len("refs/heads/"):]
    todo = []
    for path, known in REMOVE.items():
        have = blob_at(tip, path)
        if have == known:
            todo.append(("D", path, None))
        elif have:
            skipped.append((branch, path, have, "unknown variant, left alone"))
    for path, (known, _) in REPLACE.items():
        have = blob_at(tip, path)
        if have == known:
            todo.append(("M", path, new_blob[path]))
        elif have and have != new_blob[path]:
            skipped.append((branch, path, have, "unknown variant, left alone"))
    if not todo:
        continue
    if branch == "main" or branch.startswith("lock/"):
        skipped.append((branch, ",".join(p for _, p, _ in todo), tip, "protected branch, never touched"))
        continue
    summary = " ".join(f"{k}:{p}" for k, p, _ in todo)
    if not build:
        rows.append((branch, tip, "-", summary))
        continue
    tree = git("rev-parse", f"{tip}^{{tree}}").decode().strip()
    for kind, path, oid in todo:
        tree = edit(tree, path.split("/"), oid).decode()
    lines = []
    removed = [p for k, p, _ in todo if k == "D"]
    changed = [p for k, p, _ in todo if k == "M"]
    if removed and changed:
        subject = "Remove a script that deletes src and include; tablebase download scripts refuse unsafe file names [skip ci]"
    elif removed:
        subject = "Remove a script that deletes src and include [skip ci]"
    else:
        subject = "Tablebase download scripts refuse unsafe file names [skip ci]"
    lines.append(subject)
    lines.append("")
    lines.append("Owner's instruction of 2026-11-12, after the repository safety review: no file may stay at a branch tip")
    lines.append("that can destroy data when it is run.")
    lines.append("")
    for p in removed:
        lines.append(f"- {p} removed. Run from a repository root it deleted the folders src and")
        lines.append("  include and then stopped at the placeholder path '<repo>/'.")
    for p in changed:
        lines.append(f"- {p}: every line of the checksum list must now be '<md5>  <table file name>'")
        lines.append("  with a plain Syzygy table name; any other line stops the script before a download. Before, a name")
        lines.append("  such as ../x.rtbw in the list was written outside the destination folder.")
    lines.append("")
    lines.append("Nothing else on this branch is changed. The earlier versions remain in the branch history.")
    lines.append("[skip ci] keeps this housekeeping commit from starting workflow runs.")
    commit = git("commit-tree", tree, "-p", tip, data=("\n".join(lines) + "\n").encode()).decode().strip()
    # proof: the commit differs from its parent in exactly the planned paths
    diff = sorted(l.split("\t") for l in git("diff-tree", "-r", "--no-commit-id", "--name-status", tip, commit).decode().splitlines())
    want = sorted([k, p] for k, p, _ in todo)
    if diff != want:
        raise SystemExit(f"{branch}: commit differs from the plan: {diff} != {want}")
    rows.append((branch, tip, commit, summary))

with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    for r in rows:
        f.write("\t".join(r) + "\n")
print(("built" if build else "planned"), len(rows), "branches")
for r in rows:
    print(f"  {r[0]:<40} {r[1][:10]} -> {r[2][:10]}  {r[3]}")
print("skipped:", len(skipped))
for s in skipped:
    print("  ", s)
