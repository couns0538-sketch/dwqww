# fn_diff.py OLD NEW [FUNCTION ...] - Opus R14-B: compare two versions of a Python file function by function (own code).
"""Compare two versions of relabel2.py function by function (source text of each top-level def, via ast)."""
import ast
import difflib
import sys


def functions(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


old, new = functions(sys.argv[1]), functions(sys.argv[2])
same = sorted(n for n in old if n in new and old[n] == new[n])
changed = sorted(n for n in old if n in new and old[n] != new[n])
print("identical:", " ".join(same))
print("changed:", " ".join(changed))
print("only in old:", " ".join(sorted(set(old) - set(new))) or "-")
print("only in new:", " ".join(sorted(set(new) - set(old))) or "-")
for name in sys.argv[3:]:
    print(f"\n--- diff of {name}")
    sys.stdout.writelines(difflib.unified_diff(old[name].splitlines(True), new[name].splitlines(True), "frozen", "post-proof", n=1))
