#!/usr/bin/env python3
"""prediction_check_correction.py — score correction/prediction.txt against correction/out."""
import math
import statistics
import sys


def load(path):
    rows = []
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            rows.append(dict(zip(head, line.rstrip("\n").split("\t"))))
    return rows


def cell(d, mt, mo):
    rows = load(f"{d}/mt{mt}_mo{mo}.tsv")
    walls = [float(r["wall_ms"]) for r in rows]
    eng = [float(r["engine_time_ms"]) for r in rows if r["engine_time_ms"]]
    depth0 = sum(1 for r in rows if r["last_depth"] == "12")
    return dict(walls=walls, med=statistics.median(walls),
                eng=statistics.median(eng) if eng else None,
                d12=depth0, n=len(rows))


def main() -> int:
    d = sys.argv[1]
    c = {(mt, mo): cell(d, mt, mo) for mt in (50, 100, 200, 500) for mo in (0, 10, 25, 45)}
    out = []

    def add(pid, name, got, pred, lo, hi, unit):
        ok = lo <= float(got) <= hi
        out.append((pid, name, pred, got, f"{lo}..{hi}", unit, "SURVIVES" if ok else "**REFUTED**"))

    add("P1", "movetime 50, overhead 0: median WALL", round(c[(50, 0)]["med"], 1), 50, 44, 56, "ms")
    add("P2", "movetime 50, overhead 10: median WALL", round(c[(50, 10)]["med"], 1), 40, 34, 46, "ms")
    add("P3", "mo0 minus mo10 median wall", round(c[(50, 0)]["med"] - c[(50, 10)]["med"], 1), 10, 7, 13, "ms")
    add("P4", "movetime 200 mo0 vs mo10 differ by ~10", round(abs(c[(200, 0)]["med"] - c[(200, 10)]["med"]), 1),
        10, 3, 13, "ms")
    gap50 = c[(50, 0)]["med"] - (c[(50, 0)]["eng"] or 0)
    add("P5", "wall minus last-info time, movetime 50 mo0", round(gap50, 1), "1..9", 1, 9, "ms")
    differ = c[(50, 0)]["d12"] != c[(50, 10)]["d12"]
    out.append(("P6", "same last depth at mo0 and mo10 (movetime 50)",
                "yes", f"d12 counts {c[(50,0)]['d12']} vs {c[(50,10)]['d12']}", "equal", "-",
                "**REFUTED**" if differ else "SURVIVES"))
    worst = min((v["med"] / max(1, mt - mo), f"mt{mt}_mo{mo}") for (mt, mo), v in c.items())
    out.append(("P7", "worst median/plan ratio below 0.90", "yes", f"{worst[0]:.2f} at {worst[1]}",
                "<0.90", "-", "SURVIVES" if worst[0] < 0.90 else "**REFUTED**"))
    add("P8", "overhead 45 movetime 50 (plan 5): median wall", round(c[(50, 45)]["med"], 1), 5, 2, 20, "ms")
    longest = max(c, key=lambda k: c[k]["med"] / max(1, k[0] - k[1]))
    out.append(("P9", "largest undershoot at the longest movetime", "no",
                f"largest ratio deficit at movetime {longest[0]}", "not 500", "-",
                "SURVIVES" if longest[0] != 500 else "**REFUTED**"))

    print("| id | measurement | predicted | measured | kill range | verdict |")
    print("|---|---|---|---|---|---|")
    for pid, name, pred, got, rng, unit, verdict in out:
        print(f"| {pid} | {name} | {pred} {unit} | {got} {unit} | {rng} | {verdict} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
