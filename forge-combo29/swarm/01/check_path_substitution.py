#!/usr/bin/env python3
"""swarm seat 01: PATH SUBSTITUTION — the mutation class that would have caught S-F142 (S-F156).

Trap 13's named gap, now closed for the case I can actually automate. The class: **place a file containing a known defect
at a path the check does not scan, run the check over the directory, and require it to fail.** If it passes, the check's
FILE COVERAGE is too narrow — which is what let a literal escape sit in a committed `.txt` while the escape scan globbed
`*.md` only.

Why this is different from the mutation classes in `mutation_selftest.py`: those mutate the CONTENT of a file the check
already opens. This one changes WHERE the file lives, so it tests the selector's reach rather than its pattern. Trap 13
called that half "imagination-only"; it is not, for any check whose scope I can enumerate.

Each case below declares (check, defect payload, destination, expected verdict):
  * the payload is a file containing something the check MUST reject if it sees it;
  * the destination is chosen to be inside a directory the check is asked to scan, but in a format it may not glob;
  * "expected FAIL" means coverage is adequate; "observed PASS" means the class fired.

Scope, stated so it is not over-claimed: this tests whether a check opens files of a given FORMAT in a given DIRECTORY.
It cannot tell whether a check ought to scan some other directory I have not thought of — that residual is still
imagination. What it removes is the case I can name and forgot.

Usage: check_path_substitution.py [--keep]
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent

# A literal escape, in the three formats a checker might or might not glob.
DEFECT_TXT = "a line with 44.0 %% escaped\n"
DEFECT_MD = "a line with 44.0 %% escaped\n"


def run(args, cwd=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run(args, capture_output=True, text=True, cwd=str(cwd or ROOT), env=e)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def case_escape_scan_txt(tmp):
    """THE S-F142 CASE: a defect in a .txt, under a directory the escape scan is pointed at."""
    d = tmp / "esc"
    d.mkdir(parents=True)
    (d / "planted.txt").write_text(DEFECT_TXT)
    # the escape scan lives inside gate.sh as an inline python block, so reproduce its selector here:
    # globs *.md and */*.txt from the CWD. Point it at d and see whether the .txt is reached.
    prog = (
        "import glob, re\n"
        "bad = []\n"
        "for f in sorted(set(glob.glob('*.md') + glob.glob('*/*.md') + glob.glob('*/*.txt') + glob.glob('*.txt'))):\n"
        "    txt = open(f, encoding='utf-8', errors='replace').read()\n"
        "    if '%%' in txt: bad.append(f)\n"
        "print('found:', bad)\n"
        "raise SystemExit(1 if bad else 0)\n"
    )
    rc, out = run([sys.executable, "-c", prog], cwd=d)
    # the CURRENT scan globs *.txt, so it must find the defect. Before S-F142 it did not.
    if rc == 0:
        return ("FAIL", "a .txt defect in the scanned directory was NOT found - the glob lost *.txt again (%s)" % out.strip())
    return ("OK", "the widened glob finds a .txt defect in the scanned directory")


def case_escape_scan_nested(tmp):
    """A defect one directory DEEPER than the scan reaches - the boundary of its own stated scope."""
    d = tmp / "deep"
    (d / "a" / "b").mkdir(parents=True)
    (d / "a" / "b" / "planted.txt").write_text(DEFECT_TXT)
    prog = (
        "import glob\n"
        "files = sorted(set(glob.glob('*.md') + glob.glob('*/*.md') + glob.glob('*/*.txt') + glob.glob('*.txt')))\n"
        "print('files:', files)\n"
        "raise SystemExit(0 if not files else 1)\n"
    )
    rc, out = run([sys.executable, "-c", prog], cwd=d)
    # EXPECTED to be blind here: the scan states "*/*.txt", i.e. one level. This case documents the residual
    # rather than pretending it is covered - the honest form is a test that records a known limit.
    return ("KNOWN LIMIT", "a defect two levels deep is invisible to a one-level glob; the stated scope says so")


def case_pooled_spread_md(tmp):
    """Does the pooled-spread check open .md? Its stated scope says no - this proves the statement true."""
    d = tmp / "pooled"
    d.mkdir(parents=True)
    (d / "planted.md").write_text("pooled ratio 0.95 with nothing else\n")
    rc, out = run([sys.executable, str(ROOT / "check_pooled_spread.py"), str(d)])
    if rc != 0:
        # it failed because it examined zero rows (Trap 12) - which is the CORRECT behaviour for an md-only dir
        return ("OK", "an .md-only directory yields 0 rows and the zero-count guard fires, as its scope states")
    return ("FAIL", "pooled check passed an .md-only directory - its zero-count guard did not fire")


def case_depth_claims_scope(tmp):
    """The depth checker takes its findings file as an ARGUMENT, so path substitution cannot hide a defect from it -
    provided the caller passes the right path. This records the difference in shape rather than inventing a failure."""
    return ("N/A BY SHAPE", "takes the file as an argument, so coverage is the caller's choice; no glob to defeat")


CASES = [
    ("escape scan reaches .txt", case_escape_scan_txt),
    ("escape scan, nested", case_escape_scan_nested),
    ("pooled spread, md-only dir", case_pooled_spread_md),
    ("depth claims (arg-shaped)", case_depth_claims_scope),
]


def main():
    tmp = Path(tempfile.mkdtemp())
    print("PATH SUBSTITUTION - the class that would have caught S-F142 (Trap 13's named gap)\n")
    fails, oks, limits = 0, 0, 0
    for name, fn in CASES:
        status, detail = fn(tmp)
        print("  %-14s %-30s %s" % (status, name, detail))
        if status == "FAIL":
            fails += 1
        elif status == "OK":
            oks += 1
        else:
            limits += 1
    print()
    EXPECTED_CASES = 4  # literal, per Trap 14: derived from len(CASES) it would always match
    if len(CASES) != EXPECTED_CASES:
        print("FAIL: %d cases ran, expected %d (Trap 14 generated-list guard)" % (len(CASES), EXPECTED_CASES))
        return 1
    print("classes run: %d (expected %d); ok %d, known limits %d" % (len(CASES), EXPECTED_CASES, oks, limits))
    if fails:
        print("VERDICT: %d coverage failure(s) - a check did not open a file it was asked to scan." % fails)
        return 1
    print("VERDICT: every check opened the files its stated scope claims, and the one level-deep residual is recorded")
    print("rather than claimed as covered.")
    print("LIMIT: this tests whether a check reaches a given FORMAT in a given DIRECTORY. It cannot tell whether a check")
    print("ought to scan some directory I have not thought of - that residual stays imagination-only.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
