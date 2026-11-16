#!/usr/bin/env python3
"""Compare the eval line of each FEN with the eval line of its colour mirror.

Reads harness_mirror.py output files, prints one line per differing position and a count
per component. Exit code 0 always; the table is the output.

usage: compare.py OUTFILE... > table.txt
"""
import sys

KEYS = ("hce", "nnue", "total")


def parse(line):
    """'info string eval hce -325 nnue -26 total -351' -> {'hce': '-325', ...} (or None)."""
    if not line or not line.startswith("info string eval"):
        return None
    tok = line.split()
    out = {}
    for k in KEYS:
        if k in tok:
            i = tok.index(k)
            if i + 1 < len(tok):
                out[k] = tok[i + 1]
    return out or None


def load(path):
    rows = {}
    with open(path) as fh:
        for raw in fh:
            parts = raw.rstrip("\n").split("\t")
            if parts[0] in ("FEN", "MIR", "EVAL", "MEVAL"):
                i = int(parts[1])
                rec = rows.setdefault(i, {})
                rec[parts[0]] = "\t".join(parts[2:])
            elif parts[0] == "FAIL":
                rows.setdefault(int(parts[1]), {})["FAIL"] = "\t".join(parts[2:])
    return rows


def main(paths):
    total_pos = 0
    diffs = []
    missing = []
    per_component = {k: 0 for k in KEYS}
    for path in paths:
        rows = load(path)
        for i in sorted(rows):
            r = rows[i]
            if "FAIL" in r:
                missing.append((path, i, r["FAIL"]))
                continue
            a, b = parse(r.get("EVAL")), parse(r.get("MEVAL"))
            if a is None or b is None:
                missing.append((path, i, "no eval line: %r / %r" % (r.get("EVAL"), r.get("MEVAL"))))
                continue
            total_pos += 1
            bad = [k for k in KEYS if a.get(k) != b.get(k)]
            for k in bad:
                per_component[k] += 1
            if bad:
                diffs.append((path, i, r["FEN"], r["MIR"], r["EVAL"], r["MEVAL"], ",".join(bad)))

    print("positions compared: %d" % total_pos)
    print("positions with a difference: %d" % len(diffs))
    print("missing/failed: %d" % len(missing))
    for k in KEYS:
        print("  positions differing in %s: %d" % (k, per_component[k]))
    if diffs:
        print("")
        print("INDEX\tFILE\tFEN\tMIRROR_FEN\tEVAL_SELF\tEVAL_MIRROR\tCOMPONENTS")
        for d in diffs:
            print("\t".join(str(x) for x in d))
    if missing:
        print("")
        print("MISSING")
        for m in missing:
            print("\t".join(str(x) for x in m))


if __name__ == "__main__":
    main(sys.argv[1:])
