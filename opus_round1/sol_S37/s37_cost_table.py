"""S37: aggregate forge_nnue_microbench runs into the per-stage cost table and check the eval checksums.

Inputs: <runs>/<config>_round<k>.json (config = <net>_<path>, e.g. lock_avx2) and <runs>/nnue_check_<net>.txt (the
archive harness nnue_check.cpp on the same FEN dump: "<net_cp> <hce_cp> <total_cp>" per line). Checks:
  - every run passed its own checks (replica, accumulator, whole-eval mismatches all 0);
  - checksums are identical across rounds and across avx2/scalar for one net;
  - net/hce/total sums and the FNV-1a of the per-position net and total sequences equal nnue_check's.
Table: per stage and config, the median over rounds of each run's median CPU ns/call (with the min..max over rounds),
and the median over rounds of the per-call (rdtsc) median and p90.

  python -I -B s37_cost_table.py --runs DIR --out-json table.json --out-md table.md
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

MASK = (1 << 64) - 1


def fnv(values) -> str:
    h = 0xCBF29CE484222325
    for v in values:
        for b in int(v).to_bytes(8, "little", signed=True):
            h = ((h ^ b) * 0x100000001B3) & MASK
    return format(h, "x")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--out-md", type=Path, required=True)
    a = ap.parse_args(argv)
    runs: dict[str, list[dict]] = {}
    for path in sorted(a.runs.glob("*_round[0-9]*.json")):
        if path.name.endswith(".time.json"):
            continue
        m = re.fullmatch(r"(.+)_round(\d+)\.json", path.name)
        runs.setdefault(m.group(1), []).append(json.loads(path.read_text(encoding="utf-8")))
    problems, checks = [], {}
    for net in sorted({c.rsplit("_", 1)[0] for c in runs}):
        ref_path = a.runs / f"nnue_check_{net}.txt"
        rows = [list(map(int, line.split())) for line in ref_path.read_text(encoding="ascii").splitlines()]
        ref = {"lines": len(rows), "net_sum": sum(r[0] for r in rows), "hce_sum": sum(r[1] for r in rows),
               "total_sum": sum(r[2] for r in rows), "net_fnv": fnv(r[0] for r in rows), "total_fnv": fnv(r[2] for r in rows)}
        sums = set()
        for config in (c for c in runs if c.rsplit("_", 1)[0] == net):
            for run in runs[config]:
                if not run["checks"]["pass"]:
                    problems.append(f"{config}: own checks failed")
                cs = run["checksums"]
                sums.add((cs["net_sum"], cs["hce_sum"], cs["total_sum"], cs["net_fnv"], cs["total_fnv"], cs["child_net_sum"]))
        mine = sorted(sums)
        equal = len(mine) == 1 and mine[0][:5] == (ref["net_sum"], ref["hce_sum"], ref["total_sum"], ref["net_fnv"], ref["total_fnv"])
        if not equal:
            problems.append(f"{net}: microbench checksums {mine} != nnue_check {ref}")
        checks[net] = {"nnue_check": ref, "microbench_distinct_checksum_sets": len(mine), "equal_to_nnue_check": equal,
                       "child_net_sum": mine[0][5] if mine else None}
    stages = list(next(iter(runs.values()))[0]["stages"].keys())
    table = {}
    for config, rs in sorted(runs.items()):
        table[config] = {}
        for s in stages:
            cpu = [r["stages"][s]["cpu_ns_median"] for r in rs]
            table[config][s] = {
                "calls_per_pass": rs[0]["stages"][s]["calls_per_pass"],
                "cpu_ns": statistics.median(cpu), "cpu_ns_min": min(cpu), "cpu_ns_max": max(cpu),
                "call_ns_median": statistics.median(r["stages"][s]["call_ns_median"] for r in rs),
                "call_ns_p90": statistics.median(r["stages"][s]["call_ns_p90"] for r in rs),
                "rounds": len(rs)}
    report = {"tool": "s37_cost_table", "checks": checks, "problems": problems, "pass": not problems, "table": table,
              "meta": {c: {"path": rs[0]["path"], "net_w2_b2_fnv": rs[0]["net_w2_b2_fnv"], "tsc_ghz": [r["tsc_ghz"] for r in rs],
                           "positions": rs[0]["positions"], "pairs": rs[0]["pairs"]} for c, rs in runs.items()}}
    a.out_json.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    configs = sorted(runs)
    lines = ["| stage | calls/pass | " + " | ".join(f"{c} CPU ns (min..max)" for c in configs) + " | " +
             " | ".join(f"{c} per-call med/p90" for c in configs) + " |",
             "|---|---|" + "---|" * (2 * len(configs))]
    for s in stages:
        cells = [f"{table[c][s]['cpu_ns']:.1f} ({table[c][s]['cpu_ns_min']:.1f}..{table[c][s]['cpu_ns_max']:.1f})" for c in configs]
        calls = [f"{table[c][s]['call_ns_median']:.0f}/{table[c][s]['call_ns_p90']:.0f}" for c in configs]
        lines.append(f"| {s} | {table[configs[0]][s]['calls_per_pass']:,} | " + " | ".join(cells) + " | " + " | ".join(calls) + " |")
    a.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(json.dumps({"checks": checks, "problems": problems}, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
