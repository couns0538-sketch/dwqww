#!/usr/bin/env python3
"""check_custom_exceptions.py <dir> [<dir> ...]

Every custom exception a file RAISES must also be DEFINED in that file (or imported).

WHY THIS EXISTS. `job3/f2_harness_can_fail.py` raised `Missing` four times and never defined it. Any run
reaching one of those raises would have died with `NameError: name 'Missing' is not defined` — and the file is
one of the harnesses whose entire purpose is to prove a harness CAN fail, so it would have failed for the wrong
reason and looked like a detection. It sat uncommitted for hours; the check existed in METHOD_NOTES as a
one-liner for other people's harnesses and had never been run over my own folder.

WHAT COUNTS AS A CUSTOM EXCEPTION. A name raised with `raise NAME(...)` or `raise NAME` that is not a builtin
exception. Builtins are excluded so `raise ValueError(...)` does not need a definition.

TWO CONTROLS, because a checker that cannot fail is the failure mode this whole file is about:
  1. a file containing `raise Missing(...)` with no `class Missing` must be REPORTED
  2. a file containing both must NOT be reported
Both run before the real scan, on temporary files, and a failure aborts.
"""
import argparse
import builtins
import os
import re
import sys
import tempfile

BUILTIN_EXC = {n for n in dir(builtins) if isinstance(getattr(builtins, n), type)
               and issubclass(getattr(builtins, n), BaseException)}

RAISE_RE = re.compile(r"raise\s+([A-Za-z_][A-Za-z_0-9]*)")
# re.M matters: without it `^` only matches at the start of the whole file, so NO definition is ever
# found and every raiser is reported. The first version of this file was missing it and produced 25 false
# positives on 45 files - a checker that reports a confident wrong answer, which is the failure mode this
# script exists to catch. Caught by asking why a file with `class Missing` on line 25 was reported.
DEF_RE = re.compile(r"^\s*(?:class|def)\s+([A-Za-z_][A-Za-z_0-9]*)|^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=\s*\w*Error",
                    re.M)


def customs_in(src):
    """Custom exception names raised in this source and not defined or imported in it.

    Uses `ast`, not a regex. A regex over the raw text matches the WORDS "raise Missing" inside docstrings and
    comments - which is how the first two versions of this checker reported a file as broken because its
    comments DESCRIBED the bug. That is a checker judging prose instead of code, the same mistake in miniature
    as judging a configuration by a variable name.
    """
    import ast as _ast
    try:
        tree = _ast.parse(src)
    except SyntaxError:
        return []
    raised = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Raise) and node.exc is not None:
            exc = node.exc
            if isinstance(exc, _ast.Call):
                exc = exc.func
            if isinstance(exc, _ast.Name):
                raised.add(exc.id)
    raised = {n for n in raised if n not in BUILTIN_EXC and n not in ("SystemExit", "KeyboardInterrupt")}
    if not raised:
        return []
    defined = set()
    for m in DEF_RE.finditer(src):
        defined.add(m.group(1) or m.group(2))
    # also accept an import that brings the name in
    for n in list(raised):
        if re.search(r"^(?:from\s+\S+\s+)?import\s+.*\b%s\b" % re.escape(n), src, re.M):
            defined.add(n)
    return sorted(raised - defined)


def run_controls():
    ok = True
    tmp = tempfile.mkdtemp(prefix="chkexc_")

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    bad = os.path.join(tmp, "bad.py")
    open(bad, "w").write("def f():\n    raise Missing('x')\n")
    good = os.path.join(tmp, "good.py")
    open(good, "w").write("class Missing(Exception):\n    pass\n\ndef f():\n    raise Missing('x')\n")
    builtin_only = os.path.join(tmp, "b.py")
    open(builtin_only, "w").write("def f():\n    raise ValueError('x')\n")

    print("controls:")
    chk("1 raise-without-class IS reported", customs_in(open(bad).read()) == ["Missing"])
    chk("2 raise-with-class is NOT reported", customs_in(open(good).read()) == [])
    chk("3 builtin exceptions are exempt", customs_in(open(builtin_only).read()) == [])
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    a = ap.parse_args()

    if not run_controls():
        print("\nCONTROLS FAILED - refusing to scan")
        sys.exit(2)

    bad_total = 0
    scanned = 0
    for d in a.dirs:
        for root, _, files in os.walk(d):
            if "/.git" in root:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(root, fn)
                try:
                    src = open(p, encoding="utf-8", errors="replace").read()
                except Exception:
                    continue
                scanned += 1
                miss = customs_in(src)
                if miss:
                    bad_total += len(miss)
                    print("  %s: raises %s but never defines it" % (p, ", ".join(miss)))

    print("\nscanned %d .py files; %d undefined custom exception(s)" % (scanned, bad_total))
    if bad_total:
        print("FAILURE - a harness that raises an undefined name does not fail, it CRASHES,")
        print("and a crash in a failure-detection harness looks like a detection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
