#!/usr/bin/env python3
"""pc_honesty.py — seat 20: check the PC r15 build against every number file 5 publishes.

File 5's table (fresh process for each line):
  settings              bench 11   bench 13   bench 16   go perft 5
  none (no setoption)     312866     862329    3024920      4865609
  S14                     242796     656517       -            -
  PC20                    278024     587276       -            -

PC20 = S14's 14 settings, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
       MateAlphaGuard true, OwnBook false (Threads 1, Hash 16).

Every option name is checked against the exe's own `uci` list first; `unknown option`, `invalid value` and
`ERROR` are fatal.

usage: pc_honesty.py <exe> <outdir>
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]
PC20 = [("Threads", 1), ("Hash", 16)] + S14 + PC20_EXTRA

EXPECT = {
    "none": {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609},
    "S14": {"bench11": 242796, "bench13": 656517},
    "PC20": {"bench11": 278024, "bench13": 587276},
}


def uci_options(exe):
    e = Engine(exe)   # Engine sends uci and waits for uciok
    try:
        with e.lock:
            lines = list(e.lines)
    finally:
        e.close()
    names = [l.split("option name ", 1)[1].split(" type ")[0]
             for l in lines if l.startswith("option name ")]
    return names


def bench_line(exe, opts, cmd):
    e = Engine(exe, opts=opts)
    try:
        e.isready()
        k = e.mark()
        e.send(cmd)
        tok = "bench depth" if cmd.startswith("bench") else "nodes "
        import time
        t0 = time.monotonic()
        while time.monotonic() - t0 < 600:
            new = e.since(k)
            if cmd.startswith("bench") and any("bench depth" in x for x in new):
                break
            if not cmd.startswith("bench") and any(x.startswith("nodes ") for x in new):
                break
            time.sleep(0.01)
        new = e.since(k)
    finally:
        e.close()
    bad = [x for x in new if "unknown option" in x or "invalid value" in x or "ERROR" in x]
    if bad:
        raise SystemExit(f"REFUSED/ERROR lines: {bad[:3]}")
    if cmd.startswith("bench"):
        line = [x for x in new if "bench depth" in x][-1]
        return int(line.split("nodes ")[1].split()[0]), line
    line = [x for x in new if x.startswith("nodes ")][-1]
    return int(line.split()[1]), line


opts_available = set(uci_options(EXE))
print(f"exe {EXE}")
print(f"options listed: {len(opts_available)}")
all_needed = {n for n, _ in PC20}
missing = sorted(all_needed - opts_available)
print(f"options PC20 needs that are MISSING from the uci list: {missing if missing else 'none'}")
print()

rows = []
print(f"{'settings':8s} {'check':9s} {'got':>9s} {'expected':>9s} {'verdict'}")
for label, opts in (("none", []), ("S14", [("Threads", 1), ("Hash", 16)] + S14), ("PC20", PC20)):
    for cmd, key in (("bench 11", "bench11"), ("bench 13", "bench13"),
                     ("bench 16", "bench16"), ("go perft 5", "perft5")):
        exp = EXPECT[label].get(key)
        if exp is None:
            continue
        got, line = bench_line(EXE, opts, cmd)
        verdict = "MATCH" if got == exp else f"DIFFERS ({got - exp:+d})"
        rows.append({"settings": label, "check": key, "got": got, "expected": exp,
                     "match": got == exp, "line": line})
        print(f"{label:8s} {key:9s} {got:9d} {exp:9d} {verdict}")

with open(os.path.join(OUT, "pc_honesty.json"), "w") as f:
    json.dump({"exe": EXE, "options": sorted(opts_available), "rows": rows}, f, indent=1)
n_match = sum(1 for r in rows if r["match"])
print(f"\n{n_match}/{len(rows)} published numbers reproduced.")
