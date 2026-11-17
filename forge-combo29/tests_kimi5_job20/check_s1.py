#!/usr/bin/env python3
"""kimi5 job 20 Step 1 checker.
(a) Verifies each setting's sum and first-three rows against file 20's known answers.
(b) Identity: snd0 and gcd0 must equal base PER POSITION (nodes AND best move).
(c) Prints per ON setting how many positions change the node count vs base.
Reads rows/<tag>.json files. usage: check_s1.py <rowsdir>
"""
import json
import sys

ROWS = sys.argv[1]

KNOWN = {  # setting: (O sum, O first3, G sum, G first3)
    "base": (8315168, [21812, 26844, 35173], 17611204, [31779, 46086, 84457]),
    "cfb230": (8354110, [21812, 26844, 35168], 17566677, [35346, 46072, 61969]),
    "snd32": (8153620, [21833, 19490, 35333], 17928118, [32815, 46309, 84912]),
    "gcd32": (8439842, [21135, 21747, 29803], 17304549, [37292, 38190, 67899]),
    "all3": (8582039, [21139, 22060, 30503], 16979165, [30282, 42231, 59425]),
}

def load(tag):
    with open(f"{ROWS}/{tag}.json") as f:
        return json.load(f)

ok = True
data = {}
for s in ["base", "cfb230", "snd32", "gcd32", "all3", "snd0", "gcd0"]:
    for setname in ["O", "G"]:
        data[(s, setname)] = load(f"{s}_{setname}_d12")

for s, (osum, of3, gsum, gf3) in KNOWN.items():
    o, g = data[(s, "O")], data[(s, "G")]
    for got, want, label in [(o["nodes_sum"], osum, "O sum"), (o["nodes_first3"], of3, "O first3"),
                             (g["nodes_sum"], gsum, "G sum"), (g["nodes_first3"], gf3, "G first3")]:
        status = "OK" if got == want else "MISMATCH"
        if got != want:
            ok = False
        print(f"{s:7s} {label:9s} {got}  known {want}  {status}")

print()
for s0 in ["snd0", "gcd0"]:
    for setname, n in [("O", 200), ("G", 353)]:
        a, b = data[(s0, setname)], data[("base", setname)]
        eq_nodes = sum(1 for x, y in zip(a["per_position"], b["per_position"]) if x == y)
        eq_bm = sum(1 for x, y in zip(a["bestmove"], b["bestmove"]) if x == y)
        both = sum(1 for x, y, u, v in zip(a["per_position"], b["per_position"], a["bestmove"], b["bestmove"])
                   if x == y and u == v)
        if both != n:
            ok = False
        print(f"identity {s0} == base on {setname}: nodes equal {eq_nodes}/{n}, best moves equal {eq_bm}/{n}, both {both}/{n}")

print()
for s in ["cfb230", "snd32", "gcd32", "all3"]:
    line = f"{s:7s} changes vs base (node count): "
    for setname, n in [("O", 200), ("G", 353)]:
        a, b = data[(s, setname)], data[("base", setname)]
        ch = sum(1 for x, y in zip(a["per_position"], b["per_position"]) if x != y)
        line += f"{setname} {ch}/{n}   "
    print(line)

print()
print("ALL KNOWN ANSWERS MET" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
