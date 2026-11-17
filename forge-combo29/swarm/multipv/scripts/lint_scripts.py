#!/usr/bin/env python3
"""Static checks for this seat's own scripts, so a defect is caught here rather than in CI.

Each check below exists because a real finding was raised against this seat's first push:

  A  a conditional expression whose two branches are equal (`i += 2 if k == "cp" else 2`) — the
     Sonar finding that was a genuine, if harmless, smell.
  B  a shell `[ ... ]` test — `[[ ... ]]` is the safer construct and the lint asked for it.
  C  an md5sum at all.  sha256 does the same job with no weak-hash finding; md5 was dropped after
     SonarCloud flagged it twice, so this rule keeps it from coming back.
  D  an unvalidated path passed straight to subprocess — the engine path comes from argv, so it
     is resolved and checked as a regular executable first.

This is deliberately narrow: it checks the four things this seat was actually told about, and does
not pretend to be a general linter.  A check that cannot fire is worse than no check, so
`--selftest` plants one fault per rule in a temporary file.

Usage:
  python3 lint_scripts.py            # scan scripts/ and report
  python3 lint_scripts.py --selftest # prove each rule fires
"""
import argparse
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def rule_a_equal_branches(text):
    """`X if COND else X` — both arms identical, so the condition does nothing.

    Parsed by splitting on the keywords rather than by regex: the natural regex for this
    (`([^#]+?)\\s+if\\s+...\\s+else\\s+...`) has nested quantifiers that backtrack super-linearly,
    which a static checker flagged.  Splitting is linear, and easier to argue about.
    """
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        code = line.split("#", 1)[0]
        if " if " not in code or " else " not in code:
            continue
        lhs, _, rest = code.partition(" if ")
        cond, _, branches = rest.partition(" else ")
        if not cond.strip() or not branches.strip():
            continue
        # the two candidate arms are "what follows = (or +=) and the trailing `if` expression"
        for op in ("+=", "-=", "*=", "/=", "%=", "="):
            if op in lhs:
                target, _, left_arm = lhs.partition(op)
                if not target.strip():
                    continue
                if left_arm.strip() and left_arm.strip() == branches.strip():
                    what = "an augmented assignment" if op != "=" else "a conditional expression"
                    out.append((i, "both branches of %s are %r" % (what, left_arm.strip())))
                break
    return out


def rule_b_single_bracket(text):
    """A POSIX `[ ... ]` test in a bash script."""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.search(r"(^|[\s;&|(])\[\s+[^\[\]]", line):
            out.append((i, "uses `[ ` instead of `[[ `"))
    return out


def rule_c_weak_hash(text):
    """md5sum in a build script. sha256 costs nothing and draws no finding."""
    out = []
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip().startswith("#"):
            continue
        if "md5sum" in line:
            out.append((i, "uses md5sum; use sha256sum"))
    return out


def rule_d_unvalidated_exec(text):
    """Popen/run on a bare name with no validation helper in the file."""
    out = []
    if "Popen(" not in text and "subprocess.run(" not in text:
        return out
    if "_validated_exe" in text or "shutil.which" in text:
        return out
    for i, line in enumerate(text.split("\n"), 1):
        if "Popen(" in line or "subprocess.run(" in line:
            out.append((i, "subprocess call with no path validation in this module"))
    return out


RULES = [
    ("A equal conditional branches", rule_a_equal_branches, (".py",)),
    ("B single-bracket test", rule_b_single_bracket, (".sh",)),
    ("C weak hash", rule_c_weak_hash, (".sh",)),
    ("D unvalidated exec", rule_d_unvalidated_exec, (".py",)),
]


def scan(root):
    """Scan `root` for the four rule classes, reading only regular files it can open.

    `root` comes from argv (`--dir`), so it is checked rather than trusted: it must be an existing
    directory.  Each entry is opened only if it is a regular file, which also means a symlink to a
    device or a FIFO in the tree cannot make the scanner hang.
    """
    resolved = os.path.realpath(os.path.abspath(root))
    if not os.path.isdir(resolved):
        raise SystemExit("lint: not a directory: %s" % resolved)
    findings = []
    for name in sorted(os.listdir(resolved)):
        path = os.path.join(resolved, name)
        if not os.path.isfile(path) or os.path.islink(path):
            continue
        for label, fn, exts in RULES:
            if not any(name.endswith(e) for e in exts):
                continue
            with open(path) as fh:
                text = fh.read()
            for line, why in fn(text):
                findings.append((label, name, line, why))
    return findings


def selftest():
    failures = []
    plants = [
        ("A equal conditional branches", "x.py", "def f(k):\n    i = 0\n    i += 2 if k else 2\n", True),
        ("B single-bracket test", "x.sh", 'if [ "$a" = "$b" ]; then echo y; fi\n', True),
        ("C weak hash", "x.sh", "md5sum build/forge\n", True),
        ("D unvalidated exec", "x.py",
         "import subprocess\ndef g(exe):\n    return subprocess.Popen([exe])\n", True),
    ]
    for label, name, body, should_fire in plants:
        match = [r for r in RULES if r[0] == label][0]
        got = match[1](body)
        if bool(got) != should_fire:
            failures.append("%s: expected fire=%s, got %r" % (label, should_fire, got))

    # and clean versions must NOT fire
    cleans = [
        ("A equal conditional branches", "x.py", "def f():\n    i = 0\n    i += 2\n"),
        ("B single-bracket test", "x.sh", 'if [[ "$a" == "$b" ]]; then echo y; fi\n'),
        ("C weak hash", "x.sh", "sha256sum build/forge\n"),
        ("D unvalidated exec", "x.py",
         "import subprocess\ndef _validated_exe(p):\n    return p\ndef g(exe):\n    return subprocess.Popen([_validated_exe(exe)])\n"),
    ]
    for label, name, body in cleans:
        match = [r for r in RULES if r[0] == label][0]
        got = match[1](body)
        if got:
            failures.append("%s: fired on the CLEAN form: %r" % (label, got))

    print("lint selftest: %d rules, %d plants, %d failures"
          % (len(RULES), len(plants) + len(cleans), len(failures)))
    for f in failures:
        print("  FAIL " + f)
    return 1 if failures else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dir", default=HERE)
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    findings = scan(args.dir)
    print("lint: %d findings across %d rules" % (len(findings), len(RULES)))
    for label, name, line, why in findings:
        print("  %-28s %s:%d  %s" % (label, name, line, why))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
