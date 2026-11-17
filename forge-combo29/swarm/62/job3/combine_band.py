#!/usr/bin/env python3
"""combine_band.py -- merge the band-measurement runs into ONE committed table.

measure_band.py was run twice (the first run exceeded the 260 s command cap after
writing its text output but before writing its JSON), so the authoritative table
is rebuilt from the two text outputs rather than trusted from a partial JSON.
Parsing the text rather than the JSON also means the table cannot disagree with
what was actually printed.

Usage: combine_band.py --parts band_p2.txt band_p2_tail.txt --json band_p2_tail.json \
                        --out band_all.txt --json-out band_all.json
"""
import argparse
import json
import sys
from collections import Counter


def parse_text(path):
    rows = []
    with open(path) as f:
        for line in f:
            if "H=" not in line:
                continue
            parts = line.split()
            i = next(k for k, p in enumerate(parts) if p.startswith("H="))

            def val(tok):
                return int(tok.split("=", 1)[1])

            eng = " ".join(parts[i + 4:-1]).replace("engine=", "").strip()
            rows.append({
                "base": " ".join(parts[:i]),
                "H": val(parts[i]),
                "p": val(parts[i + 1]),
                "j0": val(parts[i + 2]),
                "predicted": parts[i + 3].split("=", 1)[1],
                "engine_score": eng,
                "actual": "FOUND" if eng.startswith("mate") else "MISSED",
                "agree": parts[-1] == "ok",
                "_from": path,
            })
    return rows


def parse_json(path):
    out = []
    for r in json.load(open(path)):
        out.append({
            "base": r["base"], "H": r["H"], "p": r["p"], "j0": r["j0"],
            "predicted": r["predicted"],
            "engine_score": "%s %s" % (r["score"][0], r["score"][1]),
            "actual": "FOUND" if r["score"][0] == "mate" else "MISSED",
            "agree": r["agree"], "_from": path,
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", nargs="+", default=[])
    ap.add_argument("--jsons", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--json-out", required=True)
    args = ap.parse_args()

    rows = []
    for p in args.parts:
        rows += parse_text(p)
    for p in args.jsons:
        rows += parse_json(p)

    # de-duplicate by (position, clock): a fixture measured twice counts once
    seen = {}
    for r in rows:
        seen[(r["base"], r["H"])] = r
    rows = sorted(seen.values(), key=lambda r: (r["p"], r["base"], r["H"]))

    with open(args.out, "w") as f:
        f.write("%-52s %-3s %-2s %-3s %-7s %-10s %-6s %s\n" % (
            "position", "H", "p", "j0", "predict", "engine", "actual", "match"))
        for r in rows:
            f.write("%-52s %-3d %-2d %-3d %-7s %-10s %-6s %s\n" % (
                r["base"], r["H"], r["p"], r["j0"], r["predicted"],
                r["engine_score"], r["actual"], "ok" if r["agree"] else "MISMATCH"))
        f.write("\n")

        total = len(rows)
        agree = sum(1 for r in rows if r["agree"])
        missed_pred = [r for r in rows if r["predicted"] == "MISSED"]
        missed_act = sum(1 for r in missed_pred if r["actual"] == "MISSED")
        found_pred = [r for r in rows if r["predicted"] == "FOUND"]
        found_act = sum(1 for r in found_pred if r["actual"] == "FOUND")

        f.write("(position, clock) pairs measured      : %d\n" % total)
        f.write("prediction matched engine             : %d / %d\n" % (agree, total))
        f.write("pairs predicted MISSED                : %d\n" % len(missed_pred))
        f.write("  of those, engine actually missed    : %d\n" % missed_act)
        f.write("pairs predicted FOUND                 : %d\n" % len(found_pred))
        f.write("  of those, engine actually found     : %d\n" % found_act)
        f.write("\nper clock:\n")
        c = Counter((r["H"], r["predicted"], r["actual"]) for r in rows)
        for k in sorted(c):
            f.write("  H=%d predicted=%-6s actual=%-6s count=%d\n" % (
                k[0], k[1], k[2], c[k]))

    json.dump(rows, open(args.json_out, "w"), indent=1)
    print(open(args.out).read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
