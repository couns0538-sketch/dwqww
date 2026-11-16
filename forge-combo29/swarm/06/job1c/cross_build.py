#!/usr/bin/env python3
"""Cross-build comparison: does the PC r15 build evaluate each position the same as the base build?

Reads the base harness output (harness_mirror.py text format: FEN/MIR/EVAL/MEVAL lines) and the PC
output (pc20_rerun.py JSON lines), matches them by position index, and compares hce / nnue / total
for the ORIGINAL position and for the mirrored one.

usage: cross_build.py BASE_GR.txt BASE_Rbig.txt PC_GR.jsonl PC_Rbig.jsonl
"""
import json
import sys

KEYS = ("hce", "nnue", "total")


def parse_eval_line(line):
    if not line or not line.startswith("info string eval"):
        return None
    tok = line.split()
    out = {}
    for k in KEYS:
        if k in tok:
            out[k] = int(tok[tok.index(k) + 1])
    return out if len(out) == 3 else None


def load_base(paths):
    rows = {}
    for path in paths:
        for raw in open(path):
            parts = raw.rstrip("\n").split("\t")
            if parts[0] in ("FEN", "EVAL", "MEVAL"):
                rows.setdefault(int(parts[1]), {})[parts[0]] = "\t".join(parts[2:])
    return rows


def load_pc(paths):
    rows = {}
    for path in paths:
        for raw in open(path):
            r = json.loads(raw)
            rows[r["index"]] = r
    return rows


def main():
    bgr, brb, pgr, prb = sys.argv[1:5]
    base = load_base([bgr, brb])
    pc = load_pc([pgr, prb])
    common = sorted(set(base) & set(pc))
    diffs = []
    missing = len(set(base) ^ set(pc))
    for i in common:
        b = base[i]
        p = pc[i]
        be, bm = parse_eval_line(b.get("EVAL")), parse_eval_line(b.get("MEVAL"))
        pe, pm = p["self"], p["mirror"]
        for label, x, y in (("self", be, pe), ("mirror", bm, pm)):
            if x is None or y is None:
                continue
            bad = [k for k in KEYS if x.get(k) != y.get(k)]
            if bad:
                diffs.append((i, label, b["FEN"] if label == "self" else "", ",".join(bad),
                              {k: (x.get(k), y.get(k)) for k in bad}))
    print("positions present in BOTH builds: %d (index-symmetric-difference %d)" % (len(common), missing))
    print("positions where the two builds DISAGREE on hce/nnue/total: %d" % len(diffs))
    for d in diffs[:30]:
        print("  " + "\t".join(str(x) for x in d))
    if len(diffs) > 30:
        print("  ... %d more" % (len(diffs) - 30))


if __name__ == "__main__":
    main()
