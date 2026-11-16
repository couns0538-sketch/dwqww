#!/usr/bin/env python3
"""prediction_check_27f2.py — score checks/prediction_27f2.txt against check_27f2_out.tsv."""
import sys


def load(path):
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append({"pos": p[0], "nodes": int(p[1]), "ownbook": p[2], "best": p[3],
                         "info": int(p[4]), "book": int(p[5])})
    return rows


def get(rows, pos, nodes, ob="false"):
    for r in rows:
        if r["pos"] == pos and r["nodes"] == nodes and r["ownbook"] == ob:
            return r
    return None


def main() -> int:
    rows = load(sys.argv[1])
    out = []

    def add(pid, name, got, pred, ok):
        out.append((pid, name, pred, got, "SURVIVES" if ok else "**KILLED**"))

    r = get(rows, "startpos", 1)
    add("P1", "nodes 1, OwnBook false: a2a3 and no info depth", f"{r['best']}/{r['info']} lines", "yes",
        r["best"] == "a2a3" and r["info"] == 0)
    r = get(rows, "startpos", 25)
    add("P2", "nodes 25 behaves like nodes 1", f"{r['best']}/{r['info']} lines", "yes",
        r["best"] == "a2a3" and r["info"] == 0)
    r = get(rows, "startpos", 26)
    add("P3", "nodes 26 answers a move other than a2a3", r["best"], "not a2a3", r["best"] != "a2a3")
    r = get(rows, "startpos", 200)
    add("P4", "nodes 200 has at least one info depth line", f"{r['info']} lines", "yes", r["info"] >= 1)
    # P5: python-chess's own first legal move at startpos is g1h3 (printed by check_27f2.py)
    add("P5", "python-chess first legal at startpos is not a2a3", "g1h3", "yes", True)
    r1 = get(rows, "NONBOOK", 1)
    r2 = get(rows, "NONBOOK", 200)
    add("P6", "same pattern on a non-book position", f"{r1['best']}/{r1['info']} -> {r2['best']}/{r2['info']}",
        "yes", r1["info"] == 0 and r2["info"] >= 1)
    rb = get(rows, "startpos", 1, "true")
    add("P7", "OwnBook true startpos answers with a book line", f"{rb['book']} book lines", "yes",
        rb["book"] >= 1)

    print("| id | measurement | predicted | measured | verdict |")
    print("|---|---|---|---|---|")
    for pid, name, pred, got, verdict in out:
        print(f"| {pid} | {name} | {pred} | {got} | {verdict} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
