# fn_diff.py OLD NEW [FUNCTION ...] - Opus R14-B: compare two versions of a Python file function by function (own code).
"""Compare two versions of relabel2.py function by function (source text of each top-level def, via ast).
usage: python -I -B fn_diff.py OLD.py NEW.py [FUNCTION ...]   (exit 2 = bad usage, a file that cannot be read or
parsed, or a FUNCTION that is not in both files)"""
import ast
import difflib
import sys


def fail(msg):
    print(f"fn_diff: {msg}", file=sys.stderr)
    sys.exit(2)


def functions(path):
    try:  # a missing or broken file used to end in a traceback (bug hunt #15)
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as e:
        fail(f"{path}: {e}")
    return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}


if len(sys.argv) < 3 or any(a.startswith("-") for a in sys.argv[1:]):
    print(__doc__)
    sys.exit(2)
old, new = functions(sys.argv[1]), functions(sys.argv[2])
for name in sys.argv[3:]:
    if name not in old or name not in new:
        fail(f"{name} is not a top-level function or class in both files")
same = sorted(n for n in old if n in new and old[n] == new[n])
changed = sorted(n for n in old if n in new and old[n] != new[n])
print("identical:", " ".join(same))
print("changed:", " ".join(changed))
print("only in old:", " ".join(sorted(set(old) - set(new))) or "-")
print("only in new:", " ".join(sorted(set(new) - set(old))) or "-")
for name in sys.argv[3:]:
    print(f"\n--- diff of {name}")
    sys.stdout.writelines(difflib.unified_diff(old[name].splitlines(True), new[name].splitlines(True), "frozen", "post-proof", n=1))
