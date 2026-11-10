"""compare_fens.py - row-by-row comparison of fixed-depth FEN result TSVs (no engine, no games).

usage: python -I -B compare_fens.py <reference.tsv> <candidate.tsv> [<candidate.tsv> ...] [--json <out.json>]

Each TSV row is: index, depth, score, nodes, bestmove (tab separated). The format is the same as
uci_driver.py fens and QA's refcache. A candidate is identical when every row matches the reference exactly.
The output gives per candidate: rows, identical rows, the first differing row (both sides), counts of node /
score / bestmove differences, and the SHA256 of each file. Exit 0 = all candidates identical, 3 = a
difference, 1 = error."""
import hashlib
import json
import sys
from pathlib import Path


def rows(p):
    out = []
    for n, line in enumerate(Path(p).read_text(encoding="ascii").splitlines()):
        f = line.split("\t")
        if len(f) != 5:
            raise SystemExit(f"{p}: line {n + 1} has {len(f)} fields")
        out.append(tuple(f))
    return out


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv):
    a = argv[1:]
    jout = None
    if "--json" in a:
        i = a.index("--json")
        jout = a[i + 1]
        del a[i:i + 2]
    if len(a) < 2:
        print(__doc__)
        return 1
    ref, cands = a[0], a[1:]
    r = rows(ref)
    res = {"reference": ref, "reference_sha256": sha(ref), "reference_rows": len(r), "candidates": []}
    ok = True
    for c in cands:
        x = rows(c)
        same = sum(1 for p, q in zip(r, x) if p == q)
        first = next((i for i, (p, q) in enumerate(zip(r, x)) if p != q), None)
        d = {"candidate": c, "sha256": sha(c), "rows": len(x), "identical_rows": same,
             "byte_identical_file": sha(c) == res["reference_sha256"],
             "node_diffs": sum(1 for p, q in zip(r, x) if p[3] != q[3]),
             "score_diffs": sum(1 for p, q in zip(r, x) if p[2] != q[2]),
             "bestmove_diffs": sum(1 for p, q in zip(r, x) if p[4] != q[4]),
             "first_difference": None if first is None else {"row": first, "reference": r[first], "candidate": x[first]}}
        d["identical"] = len(x) == len(r) and same == len(r)
        ok = ok and d["identical"]
        res["candidates"].append(d)
    res["all_identical"] = ok
    text = json.dumps(res, indent=1)
    if jout:
        Path(jout).write_text(text + "\n", encoding="ascii")
    print(text)
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
