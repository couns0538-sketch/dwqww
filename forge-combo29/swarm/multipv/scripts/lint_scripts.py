#!/usr/bin/env python3
"""Static checks for this seat's own scripts, so a defect is caught here rather than in CI.

Each check below exists because a real finding was raised against this seat's first push:

  A  a conditional expression whose two branches are equal (`i += 2 if k == "cp" else 2`) — the
     Sonar finding that was a genuine, if harmless, smell.
  B  a shell `[ ... ]` test — `[[ ... ]]` is the safer construct and the lint asked for it.
  C  an md5sum with no comment saying it is a build label, not a security control.  The hash is
     correct for its purpose; the code has to say so, or the next reader has to guess.
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
    """`X if COND else X` — both arms identical, so the condition does nothing."""
    out = []
    pat = re.compile(r"^\s*(\S+)\s*=\s*([^\n#]+?)\s+if\s+[^,\n]+?\s+else\s+([^\n#]+?)\s*$")
    for i, line in enumerate(text.split("\n"), 1):
        m = pat.match(line)
        if m and m.group(2).strip() == m.group(3).strip():
            out.append((i, "both branches of the conditional are %r" % m.group(2).strip()))
    # also catch the augmented-assignment form `i += A if c else A`
    pat2 = re.compile(r"^\s*(\S+)\s*([-+*/]=)\s*([^\n#]+?)\s+if\s+[^,\n]+?\s+else\s+([^\n#]+?)\s*$")
    for i, line in enumerate(text.split("\n"), 1):
        m = pat2.match(line)
        if m and m.group(3).strip() == m.group(4).strip():
            out.append((i, "both branches of an augmented assignment are %r"
                        % m.group(3).strip()))
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


def rule_c_md5_unexplained(text):
    """md5sum with no adjacent comment saying what the hash is for."""
    out = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "md5sum" not in line or line.strip().startswith("#"):
            continue
        window = "\n".join(lines[max(0, i - 4):i + 1]).lower()
        if not any(w in window for w in ("label", "not a security", "build label")):
            out.append((i + 1, "md5sum with no comment saying it is a build label"))
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
    ("C unexplained md5", rule_c_md5_unexplained, (".sh",)),
    ("D unvalidated exec", rule_d_unvalidated_exec, (".py",)),
]


def scan(root):
    findings = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
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
        ("C unexplained md5", "x.sh", "md5sum build/forge\n", True),
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
        ("C unexplained md5", "x.sh", "# build label, not a security control\nmd5sum build/forge\n"),
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
