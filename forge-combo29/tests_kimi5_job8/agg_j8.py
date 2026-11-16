#!/usr/bin/env python3
"""kimi5 job8 aggregator: sums every NSTEPS per-search line of a checks file
and prints how many it summed, the summed groups, and the viol counts.
Usage: agg_j8.py <checks.txt> [--rates]
With --rates it also prints probe MISSED-per-1000 tables (regret runs).
Schema (labels with their field counts) mirrors nstc::print() in NodeSteps.patch.txt.
"""
import sys

SCHEMA = [("gate", 7), ("rzt", 7), ("rzr", 7), ("rzn", 7), ("rfp", 42), ("nlt", 7), ("nlr", 7),
          ("nlv", 7), ("nleb", 42), ("nlnd", 21), ("nlnr", 7), ("nlnm", 7), ("pce", 7), ("pcc", 7),
          ("pcr", 7), ("pcn", 7), ("k4t", 3), ("k4c", 3), ("splitviol", 1), ("reg", 0), ("seen", 4),
          ("ended1", 1), ("wide", 1), ("pnodes", 1), ("rz", 14), ("rfpg", 84), ("nl", 14),
          ("nlebg", 84), ("nlndg", 42), ("pcg", 14)]
# rfp appears twice (steps part, regret part): the regret groups are renamed on the fly below.
COUNTS = {"gate": 7, "rzt": 7, "rzr": 7, "rzn": 7, "rfp": 42, "nlt": 7, "nlr": 7, "nlv": 7,
          "nleb": 42, "nlnd": 21, "nlnr": 7, "nlnm": 7, "pce": 7, "pcc": 7, "pcr": 7, "pcn": 7,
          "k4t": 3, "k4c": 3, "splitviol": 1, "reg": 0, "seen": 4, "ended1": 1, "wide": 1,
          "pnodes": 1, "rz": 14, "nl": 14, "pc": 14}
REGRET_ORDER = ["reg", "seen", "ended1", "wide", "pnodes", "rz", "rfp", "nl", "nleb", "nlnd", "pc"]
REGRET_RENAME = {"rfp": "rfpg", "nleb": "nlebg", "nlnd": "nlndg", "pc": "pcg"}
REGRET_COUNTS = {"rz": 14, "rfpg": 84, "nl": 14, "nlebg": 84, "nlndg": 42, "pcg": 14}

DC = ["d1", "d2", "d3", "d4", "d5-6", "d7-8", "d9+"]
MC = ["<1.25", "<1.5", "<2", "<3", ">=3", "m<=0"]
EB = ["<25", "<50", "<100", "<200", "<400", ">=400"]
ND = ["qsearch", "1-2", "3+"]


def parse_line(tokens):
    out = {}
    i = 0
    regret = False
    while i < len(tokens):
        tok = tokens[i]
        if tok == "reg":
            regret = True
            i += 1
            continue
        if regret and tok in REGRET_RENAME:
            name = REGRET_RENAME[tok]
            n = REGRET_COUNTS[name]
        elif tok in COUNTS:
            name, n = tok, COUNTS[tok]
        else:
            raise SystemExit(f"unknown token {tok!r} at {i} in line")
        vals = [int(x) for x in tokens[i + 1: i + 1 + n]]
        if len(vals) != n:
            raise SystemExit(f"short group {name}: got {len(vals)} of {n}")
        out[name] = vals
        i += 1 + n
    return out


def main():
    path = sys.argv[1]
    rates = "--rates" in sys.argv
    sums = {}
    nlines = 0
    k4t_viol = k4c_viol = split_viol = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("info string NSTEPS v1 "):
                continue
            groups = parse_line(line.split()[4:])
            nlines += 1
            for name, vals in groups.items():
                acc = sums.setdefault(name, [0] * len(vals))
                for j, v in enumerate(vals):
                    acc[j] += v
            k4t_viol += groups["k4t"][2]
            k4c_viol += groups["k4c"][2]
            split_viol += groups["splitviol"][0]
    print(f"lines_summed {nlines}")
    print(f"K4 lines with k4t viol: {k4t_viol}; k4c viol: {k4c_viol}; splitviol: {split_viol}")
    if nlines == 0:
        return
    print(f"k4t mine {sums['k4t'][0]} engine {sums['k4t'][1]}; k4c mine {sums['k4c'][0]} engine {sums['k4c'][1]}")
    for name, _ in SCHEMA:
        if name in sums and name not in ("k4t", "k4c"):
            print(f"{name} {' '.join(str(v) for v in sums[name])}")
    g = sums
    print(f"TOTALS gate {sum(g['gate'])} razor_try {sum(g['rzt'])} razor_ret {sum(g['rzr'])} "
          f"rfp_ret {sum(g['rfp'])} null_try {sum(g['nlt'])} null_ret {sum(g['nlr'])} "
          f"null_verif {sum(g['nlv'])} pc_entry {sum(g['pce'])} pc_caps {sum(g['pcc'])} pc_ret {sum(g['pcr'])}")
    print("rfp margin-class totals:", " ".join(f"{MC[j]}={sum(g['rfp'][i*6+j] for i in range(7))}" for j in range(6)))
    print("null eb-class totals:", " ".join(f"{EB[j]}={sum(g['nleb'][i*6+j] for i in range(7))}" for j in range(6)))
    print("null nd-class totals:", " ".join(f"{ND[j]}={sum(g['nlnd'][i*3+j] for i in range(7))}" for j in range(3)))
    if rates and "rfpg" in g:
        print(f"REGRET seen razor/rfp/null/pc: {g['seen']}; ended1 {g['ended1'][0]} wide {g['wide'][0]} pnodes {g['pnodes'][0]}")

        def table(name, n_arr, m_arr, ncol, cnames):
            print(f"rate-per-1000 {name} (missed/n, cells n<200 marked *):")
            hdr = "depth".ljust(6) + "".join(c.ljust(11) for c in cnames) + "row"
            print(hdr)
            for i in range(7):
                cells = ""
                tn = tm = 0
                for j in range(ncol):
                    n, m = n_arr[i * ncol + j], m_arr[i * ncol + j]
                    tn += n
                    tm += m
                    r = 1000.0 * m / n if n else 0.0
                    mark = "*" if n < 200 else " "
                    cells += f"{r:6.1f}{mark}({n})".ljust(11)
                rr = 1000.0 * tm / tn if tn else 0.0
                print(DC[i].ljust(6) + cells + f"{rr:6.1f} ({tn})")
            tn, tm = sum(n_arr), sum(m_arr)
            print(f"total  n {tn} missed {tm} rate {1000.0 * tm / tn if tn else 0.0:.1f}")

        table("razor", g["rz"][:7], g["rz"][7:], 1, ["rate"])
        table("rfp", g["rfpg"][:42], g["rfpg"][42:], 6, MC)
        table("null x depth", g["nl"][:7], g["nl"][7:], 1, ["rate"])
        table("null x eval-beta", g["nlebg"][:42], g["nlebg"][42:], 6, EB)
        table("null x nullsearchdepth", g["nlndg"][:21], g["nlndg"][21:], 3, ND)
        table("probcut", g["pcg"][:7], g["pcg"][7:], 1, ["rate"])


if __name__ == "__main__":
    main()
