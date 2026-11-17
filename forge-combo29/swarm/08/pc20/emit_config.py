#!/usr/bin/env python3
"""emit_config.py EXE FILE... — print the ACTUAL setoption list a harness sends, recognised by CONTENT.

History, because it is the point of this file:

  v1 (WRONG) matched a Python *shape*: an `ast.Assign` of a list of 2-tuples. Seat 27 ran it on its own harness and it
  printed `### list 'cases' ... 2 options; PC20 switches present: 0` — it had matched a list of TEST-CASE tuples, not
  an option list, and it could not see the real lists because they live in `SETTINGS = {"S14": [...], "PC20": [...]}`
  and are built by CONCATENATION (`["Hash 16","Threads 1"] + S14 + PC20X`). **A confident wrong answer is worse than
  no answer, because it looks like verification.**

  v2 (this file) fixes both defects, in the order they were raised:
    1. It recognises an option list by its CONTENTS — a string whose first word is a name the engine advertises in its
       own `uci` answer. That survives dicts, concatenation, comprehensions, f-strings, shell scripts, anything.
    2. **If it finds nothing that looks like a setoption list, it EXITS NON-ZERO.** "I checked and found nothing" must
       be distinguishable from "there was nothing to check".

Usage:
    python3 emit_config.py <engine-exe> <file.py> [file2.py ...]
    python3 emit_config.py <engine-exe> --string "Hash 16, Threads 1, CuckooRep true"

Exit codes: 0 = at least one option-name mention found and printed; 1 = none found; 2 = usage/engine error.
"""
import ast
import re
import subprocess
import sys

PC20_SWITCHES = ("CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard")


def engine_option_names(exe):
    r = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=60)
    names = []
    for line in r.stdout.splitlines():
        m = re.match(r"^option name (.+?) type ", line)
        if m:
            names.append(m.group(1))
    if not names:
        raise SystemExit("ENGINE ERROR: `%s` advertises no options in its uci answer" % exe)
    return names


def mentions_in_file(path, known):
    """Every place a known engine option name appears as the first word of a quoted string or a bare token."""
    src = open(path, errors="ignore").read()
    found = []
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value.strip()
                if v:
                    parts = v.split()
                    if parts and parts[0] in known:
                        found.append((getattr(node, "lineno", 0), v))
    except SyntaxError:
        pass
    for i, line in enumerate(src.splitlines(), 1):
        for m in re.finditer(r'["\']\s*([A-Za-z][A-Za-z0-9 _-]*?)\s+(?:value\s+)?([A-Za-z0-9_.-]+)\s*["\']', line):
            name = m.group(1).strip()
            if name in known:
                found.append((i, "%s %s" % (name, m.group(2))))
        # option names used as bare dict keys or concatenated literals
        for name in known:
            if len(name) > 6 and re.search(r'\b%s\b' % re.escape(name), line):
                found.append((i, name))
    seen = set()
    out = []
    for ln, text in found:
        k = (ln, text)
        if k not in seen:
            seen.add(k)
            out.append((ln, text))
    return out


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: emit_config.py <engine-exe> <file...> | --string \"...\"")
    exe = sys.argv[1]
    known = engine_option_names(exe)
    print("# the engine advertises %d option names; lists are recognised by these, not by Python shape" % len(known))
    print()

    any_found = False
    if sys.argv[2] == "--string":
        text = sys.argv[3]
        names = [n for n in known if re.search(r"\b%s\b" % re.escape(n), text)]
        if names:
            any_found = True
            pc20 = [n for n in names if n in PC20_SWITCHES]
            print("## option names present in the given string: %d" % len(names))
            for n in names:
                print("    %s" % n)
            print("    PC20 switches present: %d %s" % (len(pc20), pc20 if pc20 else ""))
        else:
            print("## NO option name from the engine's own list appears in the given string")
    else:
        for path in sys.argv[2:]:
            hits = mentions_in_file(path, known)
            print("### %s" % path)
            if not hits:
                print("    NO option name from the engine's uci list appears in this file.")
                print("    (It may build its options elsewhere, or set none.)")
                print()
                continue
            any_found = True
            names = sorted({h[1].split()[0] for h in hits})
            pc20 = [n for n in names if n in PC20_SWITCHES]
            print("    %d option-name mentions, %d distinct names" % (len(hits), len(names)))
            print("    PC20 switches present: %d %s" % (len(pc20), pc20 if pc20 else ""))
            # dedupe on the NAME so a pasted list looks like the list that was sent, not like the two scanners
            by_name = {}
            for _, text in hits:
                nm = text.split()[0]
                if nm not in by_name or len(text) > len(by_name[nm]):
                    by_name[nm] = text
            print("    pasteable list:")
            print("        " + ", ".join(by_name[n] for n in sorted(by_name)))
            print("    first mentions with line numbers:")
            for ln, text in hits[:8]:
                print("        line %d: %s" % (ln, text))
            print()

    if not any_found:
        print("**FAILING LOUDLY: nothing that looks like a setoption list was found in any input.**")
        print("Do not treat this run as a verification. Either the file builds its options elsewhere, or the")
        print("recogniser needs another shape — say which, rather than reporting a clean result.")
        sys.exit(1)


if __name__ == "__main__":
    main()
