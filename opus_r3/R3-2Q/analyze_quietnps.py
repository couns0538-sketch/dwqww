#!/usr/bin/env python3
"""R3-2Q table: read the quiet_nps.py JSON files (recursively under the given dirs) and print
config | rep | runner CPU | nodes equal | NPS d% [95% CI] at d16 | at d20 | A/A d16 | A/A d20 | rule (lo >= +2 at both)
for every comparison (SW = switch build vs OFF, OPT = same-exe option effect, SW_V4 = x86-64-v4 O2 row,
AA_REBUILD = second OFF build), plus a two-runner row per config/label: the mean of the two reps' mean log ratios
with se = sqrt(se1^2 + se2^2) / 2 and a Satterthwaite df.
Metric: --metric cpu_bench (default; CPU time after readyok), cpu_total (whole process, as nps_ab.py) or wall.
usage: analyze_quietnps.py <dir> [<dir> ...] [--metric cpu_bench] [--md out.md] [--json out.json]
Read-only on its inputs; run it with python -I on downloaded artifacts."""
import argparse
import glob
import json
import math
import os
import sys

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
        11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
        22: 2.074, 24: 2.064, 26: 2.056, 28: 2.048, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980, 10 ** 9: 1.960}
ORDER = ["AA", "NOZERO", "O2", "SPEEDSTACK", "S13", "LAZY", "INT16", "PROF", "ALL"]
LABELS = ["SW", "SW_V4", "OPT", "AA_REBUILD"]
PC_ROWS = {  # R3-2 (origin/opus-r3-matrix opus_r3/R3-2/REPORT.md), PC cycle-timed CPU NPS, d16 unless noted
    ("NOZERO", "SW"): "-4.16 [-4.60, -3.72]; d20 -4.39 [-4.95, -3.82]",
    ("O2", "SW"): "+0.13 [-0.24, +0.51]; d20 -0.05 [-1.23, +1.15] (other head +3.04 [+2.15, +3.94])",
    ("SPEEDSTACK", "SW"): "+0.59 [+0.09, +1.08]",
    ("S13", "SW"): "-0.70 [-1.76, +0.37]",
    ("S13", "OPT"): "-0.10 [-1.40, +1.22]",
    ("LAZY", "SW"): "+4.36 [+2.92, +5.81]",
    ("LAZY", "OPT"): "-1.05 [-2.52, +0.44]",
    ("INT16", "SW"): "+1.79 [+0.70, +2.89]",
    ("INT16", "OPT"): "-8.78 [-9.88, -7.66] (tree changes)",
    ("PROF", "SW"): "-7.24",
    ("PROF", "OPT"): "-1.10 [-2.02, -0.17]",
    ("AA", "AA"): "+0.06 [-0.66, +0.77]",
}


def t975(df):
    if df <= 1:
        return T975[1]
    keys = sorted(T975)
    for lo, hi in zip(keys, keys[1:]):
        if lo <= df <= hi:
            if df == lo:
                return T975[lo]
            w = (1 / df - 1 / hi) / (1 / lo - 1 / hi)
            return T975[hi] + w * (T975[lo] - T975[hi])
    return 1.96


pct = lambda x: (math.exp(x) - 1) * 100


def est(res):
    """metric dict from quiet_nps.py -> (mean_log, se, df) or None"""
    if not res or res.get("n", 0) < 2 or res.get("sd_log") is None or math.isnan(res["sd_log"]):
        return None
    return res["mean_log"], res["sd_log"] / math.sqrt(res["n"]), res["n"] - 1


def fmt(e):
    if e is None:
        return "n/a"
    m, se, df = e
    h = t975(df) * se
    return f"{pct(m):+.2f} [{pct(m - h):+.2f}, {pct(m + h):+.2f}]"


def lower(e):
    if e is None:
        return None
    m, se, df = e
    return pct(m - t975(df) * se)


def combine(es):
    es = [e for e in es if e is not None]
    if not es:
        return None
    k = len(es)
    m = sum(e[0] for e in es) / k
    v = sum((e[1] / k) ** 2 for e in es)
    den = sum(((e[1] / k) ** 2) ** 2 / max(e[2], 1) for e in es)
    df = v ** 2 / den if den > 0 else 10 ** 9
    return m, math.sqrt(v), df


def load(dirs):
    recs = []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "**", "nps_*.json"), recursive=True)):
            try:
                with open(path, encoding="utf-8") as f:
                    r = json.load(f)
            except (OSError, ValueError) as ex:
                print(f"skip {path}: {ex}", file=sys.stderr)
                continue
            r["_path"] = path
            recs.append(r)
    return recs


def run_values(r, depth, metric):
    """per-pair (A, B) values of one comparison at one depth, from the raw runs."""
    def val(x):
        if metric == "wall":
            return x["nps"]
        s = x["cpu_bench_s"] if metric == "cpu_bench" else x["cpu_total_s"]
        return x["nodes"] / s if s else 0.0
    a = {x["pair"]: val(x) for x in r["runs"] if x["depth"] == depth and x["side"] == "A"}
    b = {x["pair"]: val(x) for x in r["runs"] if x["depth"] == depth and x["side"] == "B"}
    return [(a[i], b[i]) for i in sorted(a) if i in b and a[i] > 0 and b[i] > 0]


def robust_txt(r, metric):
    """median per-pair B/A (%) and the run-to-run spread (max/min - 1 over all runs of one side, %) per depth."""
    med, spread = [], []
    for d in (16, 20):
        pv = run_values(r, d, metric)
        if not pv:
            continue
        ratios = sorted(math.log(b / x) for x, b in pv)
        k = len(ratios)
        m = ratios[k // 2] if k % 2 else (ratios[k // 2 - 1] + ratios[k // 2]) / 2
        med.append(f"{pct(m):+.2f}")
        sa = max(x for x, _ in pv) / min(x for x, _ in pv) - 1
        sb = max(y for _, y in pv) / min(y for _, y in pv) - 1
        spread.append(f"{max(sa, sb) * 100:.1f}")
    return " / ".join(med) or "n/a", " / ".join(spread) or "n/a"


def nodes_txt(r):
    out = []
    for d in ("16", "20"):
        s = r["summary"].get(d)
        if not s:
            continue
        if s["nodes_equal"]:
            t = "yes"
        elif r.get("expect_node_diff"):
            t = "no (tree changes: NPS only)"
        else:
            t = "MISMATCH"
        if s.get("pin_a") is False or s.get("pin_b") is False:
            t += " PIN FAIL"
        out.append(f"d{d} {t}")
    return "; ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--metric", default="cpu_bench", choices=["cpu_bench", "cpu_total", "wall"])
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    recs = load(a.dirs)
    if not recs:
        print("no nps_*.json found")
        return 1
    by = {}
    for r in recs:
        by[(r["config"], str(r["rep"]), r["label"])] = r
    reps = sorted({k[1] for k in by})
    lines = [f"metric: {a.metric} NPS, B/A - 1 in %, paired t on per-pair log ratios, 95% CI; "
             f"rule = 95% CI lower bound >= +2% at d16 AND d20",
             "",
             "median = median per-pair B/A (robust to one level-shift pair); spread = max/min - 1 of one side's runs "
             "(a quiet runner stays near 1-2%; larger means the runner changed speed during the comparison)",
             "",
             "| config | row | rep | runner CPU | nodes equal | NPS delta % [95% CI] d16 | d20 | A/A d16 | A/A d20 | rule "
             "| median d16 / d20 | spread % d16 / d20 | PC (R3-2) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    out = []
    cfgs = [c for c in ORDER if any(k[0] == c for k in by)] + sorted({k[0] for k in by} - set(ORDER))
    for cfg in cfgs:
        labels = ["AA"] if cfg == "AA" else []
        labels += [l for l in LABELS if any(k[0] == cfg and k[2] == l for k in by)]
        for lab in labels:
            per_rep = {}
            for rep in reps:
                r = by.get((cfg, rep, lab))
                if not r:
                    continue
                aa = by.get((cfg, rep, "AA"))
                e16 = est(r["summary"].get("16", {}).get("metrics", {}).get(a.metric))
                e20 = est(r["summary"].get("20", {}).get("metrics", {}).get(a.metric))
                a16 = est(aa["summary"].get("16", {}).get("metrics", {}).get(a.metric)) if aa else None
                a20 = est(aa["summary"].get("20", {}).get("metrics", {}).get(a.metric)) if aa else None
                per_rep[rep] = (e16, e20, a16, a20, r)
                l16, l20 = lower(e16), lower(e20)
                rule = "n/a" if lab.startswith("AA") else (
                    "MET" if (l16 is not None and l20 is not None and l16 >= 2 and l20 >= 2) else "not met")
                cpu = r.get("host", {}).get("cpu", "?").replace("|", "/")
                if r.get("host", {}).get("avx512_v4"):
                    cpu += " (AVX-512)"
                med, spread = robust_txt(r, a.metric)
                lines.append(f"| {cfg} | {lab} | {rep} | {cpu} | {nodes_txt(r)} | {fmt(e16)} | {fmt(e20)} | "
                             f"{fmt(a16) if lab != 'AA' else '-'} | {fmt(a20) if lab != 'AA' else '-'} | {rule} | "
                             f"{med} | {spread} | {PC_ROWS.get((cfg, lab), '') if rep == reps[0] else ''} |")
                out.append({"config": cfg, "label": lab, "rep": rep, "cpu": cpu, "nodes": nodes_txt(r),
                            "d16": fmt(e16), "d20": fmt(e20), "aa16": fmt(a16), "aa20": fmt(a20), "rule": rule,
                            "lo16": l16, "lo20": l20, "median": med, "spread": spread, "ok": r.get("ok"),
                            "path": r["_path"]})
            if len(per_rep) >= 2:
                c16 = combine([v[0] for v in per_rep.values()])
                c20 = combine([v[1] for v in per_rep.values()])
                ca16 = combine([v[2] for v in per_rep.values()])
                ca20 = combine([v[3] for v in per_rep.values()])
                l16, l20 = lower(c16), lower(c20)
                rule = "n/a" if lab.startswith("AA") else (
                    "MET" if (l16 is not None and l20 is not None and l16 >= 2 and l20 >= 2) else "not met")
                lines.append(f"| {cfg} | {lab} | both | two runners | | **{fmt(c16)}** | **{fmt(c20)}** | "
                             f"{fmt(ca16) if lab != 'AA' else '-'} | {fmt(ca20) if lab != 'AA' else '-'} | {rule} | | | |")
                out.append({"config": cfg, "label": lab, "rep": "both", "d16": fmt(c16), "d20": fmt(c20),
                            "aa16": fmt(ca16), "aa20": fmt(ca20), "rule": rule, "lo16": l16, "lo20": l20})
    bad = [r["_path"] for r in recs if not r.get("ok")]
    lines.append("")
    lines.append(f"files: {len(recs)}; runs with a node-rule or exit failure: {len(bad)}" + (f" {bad}" if bad else ""))
    text = "\n".join(lines)
    print(text)
    if a.md:
        with open(a.md, "w", newline="\n", encoding="utf-8") as f:
            f.write(text + "\n")
    if a.json:
        with open(a.json, "w", newline="\n", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
