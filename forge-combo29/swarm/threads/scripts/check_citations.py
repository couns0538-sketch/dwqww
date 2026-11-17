#!/usr/bin/env python3
"""Every `file.cpp:NNN` citation in FINDINGS.md must land on a line that looks like the
thing the sentence claims.

The record's rule: a pointer is a claim, and nothing compares it to its target. A bare
"all references resolve" check passes when the number exists but points at the wrong
line, so this resolves each citation and PRINTS the line it lands on, and also requires
a `must_contain` token where the finding supplies one.

Usage: python3 check_citations.py <FINDINGS.md> <source-root>
Exits 0 only when every citation resolves and every claimed token is present.
"""
import re
import sys

# file -> (line-or-range, token that must appear on that line)
# Hand-maintained from the claims in FINDINGS.md; a missing citation is a FAIL, not a skip.
EXPECTED = {
    ("src/uci.cpp", 611): "Searcher bench_searcher",
    ("include/forge/search.hpp", 573): "threads = 1",
    ("src/uci.cpp", 489): 'first == "perft"',
    ("src/search.cpp", 2700): "multipv > 1 || no_clock_left",
    ("src/search.cpp", 2711): "single_threaded",
    ("src/search.cpp", 2251): "root_drawn",
    ("src/search.cpp", 2392): "for (int depth = 1",
    ("src/search.cpp", 2640): "root_candidates.front()",
    ("src/uci.cpp", 527): "book.empty()",
    ("src/uci.cpp", 162): "time_since_epoch",
    ("src/uci.cpp", 258): 'command == "setoption"',
    ("src/uci.cpp", 176): "worker.join()",
    ("src/bitboard.cpp", 139): "void init()",
    ("src/nnue.cpp", 92): "static Weights instance",
    ("src/nnue.cpp", 466): "weights()",
}


def main():
    md_path, root = sys.argv[1], sys.argv[2]
    text = open(md_path).read()

    cited = set()
    for m in re.finditer(r"`?([A-Za-z0-9_/]+\.(?:cpp|hpp)):(\d+)(?:-(\d+))?`?", text):
        cited.add((m.group(1), int(m.group(2))))

    ok = True
    print(f"citations found in {md_path}: {len(cited)}")
    for path, line in sorted(cited):
        target = f"{root}/{path}"
        try:
            lines = open(target, errors="replace").read().split("\n")
        except FileNotFoundError:
            print(f"  FAIL {path}:{line}  no such file")
            ok = False
            continue
        if line < 1 or line > len(lines):
            print(f"  FAIL {path}:{line}  out of range (file has {len(lines)} lines)")
            ok = False
            continue
        content = lines[line - 1].strip()
        want = EXPECTED.get((path, line))
        if want is None:
            print(f"  WARN {path}:{line}  resolved but no expected token registered: {content[:70]}")
            ok = False
            continue
        if want not in content:
            print(f"  FAIL {path}:{line}  expected {want!r}, found: {content[:70]}")
            ok = False
        else:
            print(f"  ok   {path}:{line}  {content[:70]}")

    # every registered expectation must actually be cited, or the map is stale
    for key in EXPECTED:
        if key not in cited:
            print(f"  FAIL registered citation {key[0]}:{key[1]} is not cited in the document")
            ok = False

    print(f"VERDICT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
