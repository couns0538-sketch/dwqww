#!/usr/bin/env python3
"""check_output_collision.py <dir> [<dir> ...]

Does any script take a VARIANT argument but write a FIXED output path?

THE BUG THIS LOOKS FOR (my S-C80). `replicate_19c60.py` takes `--baseline {s14,pc20}` — two different
experiments — and wrote both to `replicate_19c60_d12_n120.json`. Running the second design **silently
overwrote** 600 cells of the first. Nothing errored, nothing warned, and the loss was only visible because
the two runs produced the same filename.

That is the same class as a settings label that does not name its settings, one level out: **a result file
whose name does not name its design is not a result file.** The question for a coordinator is whether it
generalises past one seat, and the way to answer that is to look, not to reason.

WHAT IT DETECTS, per script:
  * a file path that is written AND built from a CONSTANT string
  * while the same script accepts an argparse option with `choices=[...]` (a variant selector)
  * and that selector does not appear in the output path expression

Reported as a candidate, not a verdict: a script may legitimately write one summary per run to a fixed
name inside a per-job directory, which is why the directory is part of the report.

CONTROLS (before any scan; a checker that cannot fail is useless):
  1. a synthetic script with `--mode {a,b}` and a fixed output path MUST be reported
  2. the same script with the mode in the filename MUST NOT be reported
  3. a script with no variant argument MUST NOT be reported
"""
import argparse
import ast
import os
import sys
import tempfile


def variant_options(tree):
    """argparse option names that declare choices=[...] - i.e. a design selector."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name != "add_argument":
                continue
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            if "choices" not in kw:
                continue
            # positionals come as args[0]
            opt = None
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                opt = node.args[0].value
            if opt:
                out.append(opt.lstrip("-"))
    return out


def fixed_outputs(tree):
    """Paths whose NAME does not contain the variant - found via Assign as well as via Call.

    The second version of this function only looked at `open(...)` / `os.path.join(...)` arguments and
    therefore missed the real shape, which is `out = os.path.join(dir, "name_%d.json" % n)` followed by
    `json.dump(x, open(out, "w"))`. The literal lives in an Assign, one step away from the write. **That is
    the same "judge the appearance instead of the artifact" failure as every other checker tonight: I
    detected the shape I had in mind rather than the shape that existed.**
    """
    outs = []
    # assignments whose value is a path expression built without any variant name
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            fn = node.func if False else None
            fname = getattr(node.value.func, "attr", None) or getattr(node.value.func, "id", None)
            if fname == "join" and node.value.args:
                last = node.value.args[-1]
                names = {n.id for n in ast.walk(last) if isinstance(n, ast.Name)}
                is_fmt = (isinstance(last, ast.BinOp) and isinstance(last.op, ast.Mod)) or \
                         (isinstance(last, ast.Call) and getattr(last.func, "attr", None) == "format")
                is_fstr = isinstance(last, ast.JoinedStr)
                is_lit = isinstance(last, ast.Constant)
                if is_lit or is_fmt or (is_fstr and not names):
                    outs.append("__FIXED__")
                    outs.append("assigned path at line %d" % node.lineno)
    for node in ast.walk(tree):
        # os.path.join(..., "literal.json")  or  open("literal.json", "w")
        if isinstance(node, ast.Call):
            fname = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fname in ("open", "dump", "write_text", "write_bytes"):
                for a in node.args[:1]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        outs.append(a.value)
            if fname == "join":
                last = node.args[-1] if node.args else None
                # A path built by %-formatting, .format(), or f-string is STILL "fixed" in the sense that
                # matters here: it does not contain the VARIANT. The first version of this detector only
                # accepted a bare string literal and therefore MISSED the very bug it was written for -
                # `"replicate_19c60_d%d_n%d.json" % (depth, n)` is constant with respect to --baseline.
                names_in = {n.id for n in ast.walk(last) if isinstance(n, ast.Name)}
                if isinstance(last, ast.Constant) and isinstance(last.value, str):
                    outs.append(last.value)
                elif isinstance(last, ast.BinOp) and isinstance(last.op, ast.Mod):
                    outs.append("<%%-formatted: %s>" % ast.dump(last)[:40])
                    outs.append("__FIXED__")
                elif isinstance(last, ast.Call) and getattr(last.func, "attr", None) == "format":
                    outs.append("__FIXED__")
                elif isinstance(last, ast.JoinedStr):
                    if not names_in:
                        outs.append("__FIXED__")
    # Keep the sentinel through the filter. The previous version applied
    #     [o for o in outs if "." in os.path.basename(o)]
    # to EVERY entry, which silently discarded the "__FIXED__" marker I had just appended - so the detector
    # reported nothing on the exact script it was written for. A post-filter written for one kind of entry
    # deleted a different kind added later; that is the same defect as a control that cannot fire.
    keep = []
    for o in outs:
        if o.startswith("__FIXED__") or o.startswith("assigned path"):
            keep.append(o)
        elif "." in os.path.basename(o):
            keep.append(o)
    return keep


def scan(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except SyntaxError:
        return None
    variants = variant_options(tree)
    if not variants:
        return None
    src = open(path, encoding="utf-8", errors="replace").read()
    fixed = fixed_outputs(tree)
    # a fixed output is suspicious only if the variant name never appears near it
    risky = []
    for f in fixed:
        if f == "__FIXED__":
            risky.append("a path built without the variant name")
            continue
        if not any(v in f for v in variants):
            risky.append(f)
    if risky:
        return (variants, sorted(set(risky)))
    return None


def controls():
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print("  %-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            ok = False

    tmp = tempfile.mkdtemp(prefix="coll_")
    bad = os.path.join(tmp, "bad.py")
    open(bad, "w").write(
        "import argparse, json\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--mode', choices=['a','b'])\n"
        "a=p.parse_args()\n"
        "json.dump({}, open('out.json','w'))\n")
    good = os.path.join(tmp, "good.py")
    open(good, "w").write(
        "import argparse, json\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--mode', choices=['a','b'])\n"
        "a=p.parse_args()\n"
        "json.dump({}, open('out_%s.json' % a.mode,'w'))\n")
    plain = os.path.join(tmp, "plain.py")
    open(plain, "w").write("import json\njson.dump({}, open('out.json','w'))\n")

    print("controls:")
    chk("1 variant arg + FIXED output IS reported", scan(bad) is not None)
    chk("2 variant arg IN the filename is NOT reported", scan(good) is None)
    chk("3 no variant arg is NOT reported", scan(plain) is None)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    a = ap.parse_args()
    if not controls():
        print("\nCONTROLS FAILED - refusing to scan")
        sys.exit(2)

    hits = 0
    scanned = 0
    for d in a.dirs:
        for root, _, files in os.walk(d):
            if "/.git" in root:
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                p = os.path.join(root, fn)
                scanned += 1
                r = scan(p)
                if r:
                    hits += 1
                    variants, outs = r
                    print("  %s" % p)
                    print("      variant arg(s): %s" % ", ".join(variants))
                    print("      fixed output(s): %s" % ", ".join(outs))
    print("\nscanned %d .py files; %d candidate(s)" % (scanned, hits))
    if hits:
        print("A candidate is not necessarily a bug: a fixed name inside a per-job directory is fine.")
        print("It is a bug when one script runs TWO designs into ONE path.")


if __name__ == "__main__":
    main()
