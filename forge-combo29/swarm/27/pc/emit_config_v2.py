#!/usr/bin/env python3
"""emit_config_v2.py <script.py> [--exe PATH]

Print the ACTUAL option list a harness sends, so a finding can paste it.

This is a repair of seat 08's `emit_config.py` (kept unmodified as `emit_config_seat08.py` for the record).
Their idea is right and their tool works perfectly on their own file. Run on MY harness it printed

    ### list `cases` in pc/check_08c33_matrix.py
        2 options; PC20 switches present: 0

which is a confident wrong answer about a file that sends 17 and 22 options. Two causes, both in the matcher:

  1. FALSE POSITIVE - it matched `cases`, a list of TEST-CASE tuples, because it accepts any list of 2-tuples.
     It should only accept a list whose elements are option names the engine actually ADVERTISES.
  2. FALSE NEGATIVE - my option lists live in `SETTINGS = {"S14": [...], "PC20": [...]}`, and the matcher
     only inspects `ast.Assign` whose value is a `List`. A dict of lists is invisible to it.

And the root cause of both: **both harnesses build their option lists by CONCATENATION** -

    ["Hash 16", "Threads 1"] + S14 + PC20X

so a matcher that only accepts a bare literal list misses the normal way this is written, even in a file it
otherwise understands.

WHAT THIS VERSION DOES DIFFERENTLY
  * resolves `BinOp` concatenation (`[...] + NAME + NAME`), including names assigned earlier in the file
  * resolves `Dict` of lists, reporting each key as its own configuration
  * **FILTERS BY THE ENGINE'S ADVERTISED OPTION NAMES** when `--exe` is given, so `cases` cannot match
  * **EXITS NON-ZERO WHEN IT FINDS NOTHING** that looks like an option list - a guard that reports nothing to
    report is more useful than one that reports the wrong thing

A guard that reports a confident wrong answer is worse than one that reports nothing, because the wrong answer
looks like verification.
"""
import argparse
import ast
import re
import subprocess
import sys

PC_SWITCHES = ("CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2", "MateAlphaGuard")


def advertised(exe):
    """Option names the engine advertises in `uci`, lower-cased for comparison."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    try:
        p.stdin.write("uci\n"); p.stdin.flush()
        names = set()
        for ln in iter(p.stdout.readline, ""):
            m = re.match(r"option name (.+?) type ", ln)
            if m:
                names.add(m.group(1).strip().lower())
            if ln.strip() == "uciok":
                break
        p.stdin.write("quit\n"); p.stdin.flush()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
        return names
    except Exception:
        p.kill()
        raise


class Resolver:
    """Evaluate list expressions to flattened (name, value) pairs, without executing the module."""

    def __init__(self, tree):
        self.env = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name):
                try:
                    self.env[node.targets[0].id] = self.ev(node.value)
                except Exception:
                    pass

    def ev(self, node):
        """Return a list of ('name', 'value') strings, or raise."""
        if isinstance(node, ast.List):
            out = []
            for e in node.elts:
                if isinstance(e, ast.Tuple) and len(e.elts) == 2:
                    out.append((ast.literal_eval(e.elts[0]), str(ast.literal_eval(e.elts[1]))))
                elif isinstance(e, ast.Constant) and isinstance(e.value, str):
                    # a plain string form "Name value"
                    s = e.value.strip()
                    n, _, v = s.rpartition(" ")
                    out.append((n, v))
                else:
                    raise ValueError("not an option element")
            return out
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            raise ValueError("unknown name %s" % node.id)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self.ev(node.left) + self.ev(node.right)
        if isinstance(node, ast.JoinedStr) or isinstance(node, ast.Constant):
            raise ValueError("unsupported")
        raise ValueError("unsupported node %s" % type(node).__name__)

    def candidates(self, tree):
        """Yield (label, pairs) for every assignable object that resolves to option pairs."""
        seen = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not node.targets:
                continue
            tgt = node.targets[0]
            label = tgt.id if isinstance(tgt, ast.Name) else "?"
            # a dict of lists -> one candidate per key
            if isinstance(node.value, ast.Dict):
                for k, v in zip(node.value.keys, node.value.values):
                    try:
                        key = ast.literal_eval(k)
                    except Exception:
                        key = "?"
                    try:
                        pairs = self.ev(v)
                    except Exception:
                        continue
                    lab = "%s[%r]" % (label, key)
                    if lab not in seen:
                        seen.add(lab)
                        yield lab, pairs
                continue
            try:
                pairs = self.ev(node.value)
            except Exception:
                continue
            if label not in seen:
                seen.add(label)
                yield label, pairs


def looks_like_options(pairs, adv):
    """An option list has 2-tuples whose first element is an option NAME the engine advertises."""
    if not pairs:
        return False
    n = sum(1 for name, _ in pairs if name.strip().lower() in adv)
    return n >= max(2, int(0.8 * len(pairs)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--exe", default=None,
                    help="engine binary; when given, candidates are filtered by its advertised option names")
    a = ap.parse_args()

    tree = ast.parse(open(a.script).read())
    adv = advertised(a.exe) if a.exe else None
    r = Resolver(tree)

    shown = 0
    for label, pairs in r.candidates(tree):
        if adv is not None and not looks_like_options(pairs, adv):
            continue
        sw = [n for n, _ in pairs if n in PC_SWITCHES]
        print("### list %s in %s" % (label, a.script))
        print("    %d options; PC20 switches present: %d %s"
              % (len(pairs), len(sw), sw if sw else ""))
        print("    settings to quote in a finding:")
        print("        " + ", ".join("%s %s" % (n, v) for n, v in pairs))
        print()
        shown += 1

    if shown == 0:
        print("NO OPTION LIST FOUND in %s" % a.script)
        if adv is None:
            print("  (run with --exe so candidates can be filtered by the engine's advertised names)")
        print("  This is a FAILURE, not a clean result: a harness whose list cannot be found cannot be")
        print("  certified. Check for a list built at runtime or by a function.")
        sys.exit(1)
    print("%d option list(s) found and printed above." % shown)


if __name__ == "__main__":
    main()
