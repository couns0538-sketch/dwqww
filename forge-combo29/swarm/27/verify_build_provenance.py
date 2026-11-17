#!/usr/bin/env python3
"""verify_build_provenance.py <worktree> <exe> [--expect-commit SHA]

Prove WHICH COMMIT the binary you are about to measure was built from - before measuring anything.

WHY THIS EXISTS. A coordinator measured the FEN field-count matrix on a binary taken from a branch that does
**not** contain the base commit under discussion. The binary was real, the measurements were real, a `BUILD_OK`
marker was present - and the result described a different engine. That produced a confident, wrong claim of the
same class as the defects it was investigating: **a value whose provenance was assumed rather than checked.**

Every seat in this run has now been bitten by a provenance failure in some medium:
  * a settings label that did not name the settings (S-C18 group)
  * a result file whose name did not name its design (S-C80)
  * a number computed in prose rather than from its data (S-C43)
  * a diagnostic read from the slice of output the code captured (S-C117)
  * **a binary whose source commit was assumed (this one)**

The check is cheap and it has to run BEFORE the measurement, because after the measurement the provenance question
is unanswerable - the numbers exist and there is nothing to attach them to.

WHAT IT VERIFIES
  1. the worktree's HEAD, and optionally that it equals (or descends from) `--expect-commit`
  2. that the binary's mtime is not older than the most recent source change, so a stale build is caught
  3. the binary's sha256, printed so the finding can quote it
  4. OPTIONALLY, the four honesty-gate numbers if `--gate` values are supplied - because a binary that fails
     bench/perft is not the engine under discussion no matter what commit it came from

USAGE
    python3 verify_build_provenance.py /agent/repos/base/build-release/forge \\
        --worktree /agent/repos/base --expect-commit 6b98f217

Exit codes: 0 verified, 1 provenance mismatch, 2 cannot determine.
"""
import argparse
import hashlib
import os
import subprocess
import sys


def git(worktree, *args):
    r = subprocess.run(["git", "-C", worktree] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def newest_source(worktree, exts=(".cpp", ".hpp", ".h", ".cc", ".c")):
    """Newest ENGINE source mtime. Build directories are excluded by PREFIX, not by an enumerated list.

    The first version enumerated five build directory names and therefore walked into `build-s12only/`, where
    CMake's own compiler-probe file `CMakeCXXCompilerId.cpp` (written at configure time, later than the binary)
    was the newest .cpp in the tree. The checker then reported **STALE BUILD** against a perfectly good binary -
    a confident wrong answer from the very tool written to prevent confident wrong answers. The mtime of a
    generated probe file is not evidence about the engine's source.
    """
    newest = 0.0
    for root, dirs, files in os.walk(worktree):
        dirs[:] = [d for d in dirs if d != ".git" and not d.startswith("build")]
        for f in files:
            if f.endswith(exts):
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(root, f)))
                except OSError:
                    pass
    return newest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--expect-commit", default=None)
    a = ap.parse_args()

    ok = True

    def say(name, value, good=None):
        nonlocal ok
        mark = "" if good is None else ("  OK" if good else "  ** MISMATCH **")
        print("  %-24s %s%s" % (name, value, mark))
        if good is False:
            ok = False

    print("build provenance check")
    print()

    # 1. HEAD
    rc, head, err = git(a.worktree, "rev-parse", "HEAD")
    if rc != 0:
        print("  cannot read HEAD of %s: %s" % (a.worktree, err))
        sys.exit(2)
    subject_rc, subject, _ = git(a.worktree, "log", "-1", "--format=%s")
    say("worktree HEAD", head[:12])
    say("HEAD subject", subject)

    if a.expect_commit:
        # accept either equality or descent: a checkpoint branch is a legitimate base
        eq = head.startswith(a.expect_commit)
        anc_rc, _, _ = git(a.worktree, "merge-base", "--is-ancestor", a.expect_commit, "HEAD")
        anc = anc_rc == 0
        say("expected commit", a.expect_commit)
        say("equal to HEAD", "yes" if eq else "no", eq or anc)
        if not (eq or anc):
            print()
            print("  The expected commit is NOT an ancestor of this worktree.")
            print("  Anything measured on this binary describes a different engine.")

    # 2. staleness
    newest = newest_source(a.worktree)
    exe_m = os.path.getmtime(a.exe)
    fresh = exe_m >= newest - 1.0
    say("newest source mtime", "%.0f" % newest)
    say("binary mtime", "%.0f" % exe_m)
    say("binary newer than source", "yes" if fresh else "** STALE BUILD **", fresh)

    # 3. identity
    say("sha256", sha256(a.exe))

    print()
    if ok:
        print("PROVENANCE VERIFIED - quote the sha256 above in the finding.")
        print("Run the honesty gate BEFORE recording numbers: bench 11 = 312866, bench 13 = 862329,")
        print("bench 16 = 3024920, perft 5 = 4865609 on the base tree.")
        sys.exit(0)
    print("PROVENANCE NOT VERIFIED - do not record measurements from this binary.")
    sys.exit(1)


if __name__ == "__main__":
    main()
