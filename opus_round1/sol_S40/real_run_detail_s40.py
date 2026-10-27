#!/usr/bin/env python3
"""Detail of a real S40 merge (read-only on the merge output and the second-folder text copy).
usage: python -I -B real_run_detail_s40.py OUT_DIR SECOND_TEXT [--compare OTHER_OUT_DIR]
Reports: holdout hits by fullmove; for every game that touches the holdout, where its first hit sits (row offset in
the game, fullmove) and how many of its rows are holdout positions; dup_main by fullmove; and, with --compare, whether
two output directories are byte-identical except run_info.json and SHA256SUMS."""
import csv
import gzip
import json
import sys
from pathlib import Path


def fullmove(line):
    return int(line.split("|")[0].split()[5])


def bucket(fm):
    for lo, hi in ((1, 5), (6, 10), (11, 20), (21, 40), (41, 80)):
        if lo <= fm <= hi:
            return f"{lo}-{hi}"
    return "81+"


def main():
    out, text = Path(sys.argv[1]), Path(sys.argv[2])
    led = list(csv.DictReader(gzip.open(out / "forge_sol_S40_row_ledger_20261027.csv.gz", "rt", encoding="utf-8", newline="")))
    lines = text.read_bytes().decode("ascii").split("\n")[:len(led)]
    groups = {}
    for i, r in enumerate(led):
        groups.setdefault(int(r["group"]), []).append(i)
    res = {"rows": len(led), "groups": len(groups)}
    by_reason_fm = {}
    for i, r in enumerate(led):
        by_reason_fm.setdefault(r["reason"], {}).setdefault(bucket(fullmove(lines[i])), 0)
        by_reason_fm[r["reason"]][bucket(fullmove(lines[i]))] += 1
    res["rows_by_reason_and_fullmove"] = {k: dict(sorted(v.items(), key=lambda kv: int(kv[0].split("-")[0].rstrip("+")))) for k, v in by_reason_fm.items()}
    touch = []
    for g, rows in groups.items():
        hits = [k for k, i in enumerate(rows) if led[i]["reason"] == "holdout_position"]
        if hits:
            touch.append({"group": g, "rows": len(rows), "hits": len(hits), "first_hit_offset": hits[0],
                          "first_hit_fullmove": fullmove(lines[rows[hits[0]]]), "consecutive_from_first": all(h == hits[0] + j for j, h in enumerate(hits))})
    res["touching_games"] = len(touch)
    res["touching_first_hit_offset"] = {"0": sum(t["first_hit_offset"] == 0 for t in touch), "1-4": sum(1 <= t["first_hit_offset"] <= 4 for t in touch),
                                        "5+": sum(t["first_hit_offset"] >= 5 for t in touch)}
    res["touching_first_hit_fullmove"] = {}
    for t in touch:
        b = bucket(t["first_hit_fullmove"]); res["touching_first_hit_fullmove"][b] = res["touching_first_hit_fullmove"].get(b, 0) + 1
    res["touching_hits_per_game"] = {"1": sum(t["hits"] == 1 for t in touch), "2-5": sum(2 <= t["hits"] <= 5 for t in touch), "6+": sum(t["hits"] >= 6 for t in touch)}
    res["touching_rows_total"] = sum(t["rows"] for t in touch)
    res["touching_hits_consecutive_runs"] = sum(t["consecutive_from_first"] for t in touch)
    if len(sys.argv) > 3 and sys.argv[3] == "--compare":
        other = Path(sys.argv[4]); names = sorted(p.name for p in out.iterdir()); diff = []
        if names != sorted(p.name for p in other.iterdir()):
            diff.append("file lists differ")
        for n in names:
            if n in ("run_info.json", "SHA256SUMS"):
                continue
            if (out / n).read_bytes() != (other / n).read_bytes():
                diff.append(n)
        res["compare"] = {"other": str(other), "files_compared": len(names) - 2, "differing": diff, "identical": not diff}
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
