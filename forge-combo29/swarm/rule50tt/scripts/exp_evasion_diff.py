"""Q2 for the evasion boards: does a warm table at clock 99 change the score?

exp_evasion.py showed the shape IS reachable: a root at clock 99 with a quiet king
move puts a node at clock 100 on the PV (three of five fixtures). This file asks
whether warming the table there changes what the engine reports.

Design as everywhere else in this seat: one process per measurement, three
repeats, fresh process for every cold cell, and a same-clock warm control so a
change can be attributed to the clock rather than to warmth.

Also included: the clock-97 board the coordinator named
(`6k1/5ppp/8/8/8/8/8/R5NK b - - 97 40`, reported cp 0 vs truth -620), measured
here across clocks 94..99 so its clock dependence is visible rather than assumed.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"
DEPTH = 14
REPEAT = 3


def one(sequence, depth=DEPTH):
    e = u.Engine(SHIPPED, hash_mb=16, timeout=90.0)
    try:
        return [e.search(p, f"go depth {depth}") for p in sequence]
    finally:
        e.close()


def sig(r):
    return (r["score_kind"], r["score"], r["bestmove"])


def cells(fields, clocks, depth=DEPTH):
    """cold for every clock; warm pair (a,b); same-clock warm (b,b)."""
    out = {}
    for c in clocks:
        runs = [one([f"position fen {fields} {c} 60"], depth) for _ in range(REPEAT)]
        out[f"cold|{c}"] = {"sigs": [sig(r[0]) for r in runs], "nodes": [r[0]["nodes"] for r in runs]}
    for a in clocks:
        for b in clocks:
            if a == b:
                continue
            runs = [one([f"position fen {fields} {a} 60", f"position fen {fields} {b} 60"], depth)
                    for _ in range(REPEAT)]
            out[f"warm|{a}->{b}"] = {"sigs": [sig(r[1]) for r in runs],
                                     "nodes": [r[1]["nodes"] for r in runs]}
    for b in clocks:
        runs = [one([f"position fen {fields} {b} 60", f"position fen {fields} {b} 60"], depth)
                for _ in range(REPEAT)]
        out[f"same|{b}"] = {"sigs": [sig(r[1]) for r in runs],
                            "nodes": [r[1]["nodes"] for r in runs]}
    return out


def stable(rec):
    return len(set(rec["sigs"])) == 1 and len(set(rec["nodes"])) == 1


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/evasion_diff.json"
    result = {}

    evasions = [
        ("kq_check_99", "8/8/8/8/8/1K6/2Q5/7k b - -", [98, 99]),
        ("kr_check_99", "7k/8/8/R7/8/8/8/K7 b - -", [98, 99]),
        ("rook_check", "6k1/5ppp/8/8/8/8/8/R5NK b - -", [97, 98, 99]),
    ]
    for name, fields, clocks in evasions:
        result[name] = cells(fields, clocks)
        print(f"\n=== {name}")
        for c in clocks:
            cold = result[name][f"cold|{c}"]
            same = result[name][f"same|{c}"]
            print(f"  clock {c}: cold={cold['sigs'][0]} stable={stable(cold)} "
                  f"| same-clock warm={same['sigs'][0]} stable={stable(same)}")
            for a in clocks:
                if a == c:
                    continue
                w = result[name].get(f"warm|{a}->{c}")
                if not w:
                    continue
                ch = w["sigs"][0] != cold["sigs"][0]
                ctl = same["sigs"][0] != cold["sigs"][0]
                verdict = ("WARM CHANGED, and same-clock control also changes it"
                           if ch and ctl else
                           "WARM CHANGED, same-clock control does NOT -> clock-specific"
                           if ch else "no change")
                print(f"    warm {a}->{c}: {w['sigs'][0]}  {verdict}")

    # The named clock-97 board, swept, so its clock dependence is a measurement.
    print("\n=== the named clock-97 board, swept")
    fields = "6k1/5ppp/8/8/8/8/8/R5NK b - -"
    sweep = {}
    for c in (94, 95, 96, 97, 98, 99):
        runs = [one([f"position fen {fields} {c} 60"], DEPTH) for _ in range(REPEAT)]
        sweep[c] = {"sigs": [sig(r[0]) for r in runs], "nodes": [r[0]["nodes"] for r in runs]}
        print(f"  clock {c}: {sweep[c]['sigs'][0]} nodes={sweep[c]['nodes'][0]} stable={stable(sweep[c])}")
    result["named_board_sweep"] = {str(k): v for k, v in sweep.items()}

    json.dump(result, open(out_path, "w"), indent=1)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
