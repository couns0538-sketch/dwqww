#!/usr/bin/env python3
"""emit_config.py — print the ACTUAL option list a harness sends, so a finding can paste it.

Why this exists (08-W3): my `check_repetition_root.py` had a list VARIABLE NAMED `S14` that contained the five PC20
switches. I wrote "S14" into a finding by trusting the name. The mechanical fix is not to rename variables — it is to
PRINT the list from the same object the harness uses, and paste that printout. A list printed by the code cannot
disagree with the code.

Usage:
    python3 emit_config.py <script.py>      # prints every option-list literal found, as a pasteable block
    python3 emit_config.py --self           # prints this file's own demo list
"""
import ast
import sys


def lists_in(path):
    """Find list literals of (name, value) tuples by parsing the file — not by importing it."""
    src = open(path).read()
    tree = ast.parse(src)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            names = []
            ok = True
            for elt in node.value.elts:
                if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
                    try:
                        names.append((ast.literal_eval(elt.elts[0]), ast.literal_eval(elt.elts[1])))
                    except Exception:
                        ok = False
                        break
                else:
                    ok = False
                    break
            if ok and names:
                label = node.targets[0].id if isinstance(node.targets[0], ast.Name) else "?"
                found.append((label, names))
    return found


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--self":
        demo = [("LmrQuietBase", "93"), ("CuckooRep", "true")]
        print("setoptions this harness sends, in order:")
        for name, value in demo:
            print("    setoption name %s value %s" % (name, value))
        print("    (PC20 switches present: %s)" %
              ("YES" if any(n in ("CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard")
                            for n, _ in demo) else "no"))
        return
    if len(sys.argv) < 2:
        raise SystemExit("usage: emit_config.py <script.py> | --self")
    path = sys.argv[1]
    if not path.endswith(".py"):
        print("### %s is not a Python file — the AST scan does not apply." % path)
        print("    Grep the setoption lines instead and paste them verbatim:")
        print("        grep -o 'setoption name [A-Za-z0-9_]* value [^\"\n]*' %s" % path)
        return
    for label, names in lists_in(path):
        pc20 = [n for n, _ in names if n in ("CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard")]
        print("### list `%s` in %s" % (label, path))
        print("    %d options; PC20 switches present: %d %s" % (len(names), len(pc20), pc20 if pc20 else ""))
        print("    settings to quote in a finding:")
        print("        %s" % ", ".join("%s %s" % (n, v) for n, v in names))
        print()


if __name__ == "__main__":
    main()
