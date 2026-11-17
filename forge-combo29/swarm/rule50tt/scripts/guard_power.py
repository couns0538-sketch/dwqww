"""Is `score_usable` load-bearing ABOVE the 90 threshold?

The exact/never question. At `board.halfmove_clock() >= 90` there are two
independent gates before a TT cutoff:

  main search : `near50` (>= 90) refuses the cutoff outright, AND
                `board.halfmove_clock() < 90` appears again in the cutoff test
  qsearch     : `near50` refuses the cutoff outright

`score_usable` is evaluated before both. So above 90 there is a second guard with
the same constant, and the question is whether `score_usable` ever decides a
verdict the 90 guards would not.

This is measured, not reasoned: the trace build counts `mate` (branch B) and the
verdict counts, and `exact_mate_far` counts the exact-clock accepts where the
mate could not land. A build with `score_usable` returning true always
(`always_true`) is the differential control: if `always_true` and the shipped
build agree on every cell in a *fresh* process, then `score_usable` changed
nothing that reached the score -- which is a real result about a guard the audit
has been treating as protective.
"""
import concurrent.futures as cf
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import uci_driver as u  # noqa: E402

SHIPPED = "/agent/repos/dwqww/forge-combo29/build-rule50/forge"
ALWAYS = "/tmp/forge-variants/always_true/build/forge"
NOHORIZON = "/tmp/forge-variants/no_horizon/build/forge"
TIMEOUT = 60.0

BOARDS = [
    ("kqk_a",    "8/8/8/8/8/1K6/2Q5/7k w - -"),
    ("kqk_b",    "8/8/8/8/8/2K5/1Q6/7k w - -"),
    ("krk_far",  "7k/8/8/R7/8/8/8/K7 w - -"),
    ("krk_box",  "7k/8/1R6/8/8/8/8/K7 w - -"),
    ("krk_edge", "k7/8/8/8/8/2K5/8/7R w - -"),
    ("kp_white", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -"),
    ("kp_black", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 b - -"),
    ("mixed",    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ -"),
    ("mixed2",   "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - -"),
    ("mixed3",   "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R b KQ -"),
]
CLOCKS = [0, 50, 80, 85, 88, 89, 90, 91, 92, 95, 99]
DEPTH = 12


def one(exe, fields, clock, depth=DEPTH):
    e = u.Engine(exe, hash_mb=16, timeout=TIMEOUT)
    try:
        r = e.search(f"position fen {fields} {clock} 60", f"go depth {depth}")
        return {"kind": r["score_kind"], "score": r["score"], "bestmove": r["bestmove"],
                "nodes": r["nodes"], "invalid": r["invalid_fen"]}
    except TimeoutError:
        return {"timeout": True}
    finally:
        e.close()


def job(args):
    label, exe, fields, clock = args
    return label, one(exe, fields, clock)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/guard_power.json"
    builds = {"shipped": SHIPPED, "always_true": ALWAYS, "no_horizon": NOHORIZON}
    jobs = []
    for bname, exe in builds.items():
        for name, fields in BOARDS:
            for clock in CLOCKS:
                jobs.append((f"{bname}|{name}|{clock}", exe, fields, clock))

    res = {}
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for f in cf.as_completed([pool.submit(job, j) for j in jobs]):
            label, r = f.result()
            res[label] = r

    json.dump(res, open(out, "w"), indent=1)

    # Compare each variant to shipped, per clock, and report where they differ.
    for variant in ("always_true", "no_horizon"):
        print(f"\n=== {variant} vs shipped")
        per_clock = {}
        for name, _ in BOARDS:
            for clock in CLOCKS:
                a = res.get(f"shipped|{name}|{clock}")
                b = res.get(f"{variant}|{name}|{clock}")
                if a is None or b is None:
                    continue
                if a.get("timeout") or b.get("timeout"):
                    if a.get("timeout") != b.get("timeout"):
                        per_clock.setdefault(clock, []).append((name, "timeout", a, b))
                    continue
                if (a["kind"], a["score"], a["bestmove"]) != (b["kind"], b["score"], b["bestmove"]):
                    per_clock.setdefault(clock, []).append((name, "diff", a, b))
        for clock in CLOCKS:
            n = len(per_clock.get(clock, []))
            print(f"  clock {clock:3}: {n:2} of {len(BOARDS)} boards differ")
            for item in per_clock.get(clock, [])[:3]:
                name, kind, a, b = item
                print(f"      {name:9} shipped={a.get('kind')} {a.get('score')} {a.get('bestmove')}"
                      f"  ->  {b.get('kind')} {b.get('score')} {b.get('bestmove')}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
