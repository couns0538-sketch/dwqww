#!/usr/bin/env python3
"""kimi5 job 19 Step 3 summer: totals over ALL 'info string SNG v1' lines of each run's
_full.txt; prints how many lines it summed. Also checks node equality with the plain
build (Step 1 json sums) and the SingularDepth 20 all-zero control."""
import json, re, sys

NAMES = ["d6_7n","d6_7c","d8_9n","d8_9c","d10_11n","d10_11c","d12pn","d12pc","othern","otherc"]
CATS = ["verif","sing","dbl","trp","mc","n2","n1"]
PLAIN = {  # Step 1 plain-build sums (== job known answers)
 "base":  {"O": 8315168,  "G": 17611204},
 "snc1":  {"O": 8346403,  "G": 16793551},
 "tem100":{"O": 8436458,  "G": 19117129},
}

def parse_line(line):
    out = {}
    toks = line.split()
    i = toks.index("v1") + 1
    for k, name in enumerate(NAMES):
        vals = [int(x) for x in toks[i + 2*k + 1].split(",")]
        out[name] = dict(zip(CATS, vals))
    return out

def summer(tag):
    tot = {n: dict.fromkeys(CATS, 0) for n in NAMES}
    nlines = 0
    with open(f"rows/{tag}_full.txt") as f:
        for line in f:
            if "info string SNG v1" in line:
                nlines += 1
                d = parse_line(line)
                for n in NAMES:
                    for c in CATS:
                        tot[n][c] += d[n][c]
    return nlines, tot

def flat(tot):
    return {c: sum(tot[n][c] for n in NAMES) for c in CATS}

print(f"{'run':16s} {'lines':>5s} {'nodes ok':>9s} " + " ".join(f"{c:>8s}" for c in CATS) + "  sing/verif")
for cfg in ("base", "snc1", "tem100", "sd20"):
    for s in ("O", "G"):
        tag = f"c{cfg}_{s}_d12"
        nlines, tot = summer(tag)
        with open(f"rows/{tag}.json") as f:
            j = json.load(f)
        nsum = j["nodes_sum"]
        if cfg == "sd20":
            nok = "n/a"
        else:
            nok = "OK" if nsum == PLAIN[cfg][s] else f"MISMATCH({nsum})"
        t = flat(tot)
        share = f"{t['sing']/t['verif']:.4f}" if t["verif"] else "-"
        print(f"{tag:16s} {nlines:5d} {nok:>9s} " + " ".join(f"{t[c]:8d}" for c in CATS) + f"  {share}")

print()
print("== per-bin table (verif,sing,dbl,trp,mc,n2,n1) ==")
for cfg in ("base", "snc1", "tem100"):
    for s in ("O", "G"):
        tag = f"c{cfg}_{s}_d12"
        nlines, tot = summer(tag)
        print(f"-- {tag} ({nlines} searches summed)")
        for n in NAMES:
            v = tot[n]
            if any(v[c] for c in CATS):
                print(f"   {n:9s} " + ",".join(str(v[c]) for c in CATS))
