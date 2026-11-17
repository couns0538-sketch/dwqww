#!/usr/bin/env python3
"""kimi5 job 22 Step 1 checker: per-position equality against file 22's known row hashes,
the identity run, and per-ON-setting changed-position counts.
Row hash (file 22 head): first 16 hex of sha256 of the values in position order,
each followed by one LF. Usage: check_s1_j22.py <rows_dir>"""
import hashlib
import json
import sys

ROWS = sys.argv[1] if len(sys.argv) > 1 else "rows"

KNOWN = {
    # tag: (O_n, O_m, G_n, G_m)  from FABLE_TO_kimi5_22.md
    "base": ("fd609b7b1a8dd179", "14583c86b5f56cb6", "60b6916f01395e99", "0846f027e7e9b77e"),
    "nt3":  ("163ec0bd9bc90140", "555369f411e75bd5", "b5da8f033e46f6ce", "53678ff52ed6f21c"),
    "nc2":  ("4bc99ee17d45ade1", "e8237ae038b24511", "7ab800b9941d73c9", "77dfb085c5c1a49b"),
    "mc1":  ("3e443de62239d7ef", "18173b4af5a3a2e0", "2ee86e30605f3b86", "92540e0591a1ed48"),
    "sf":   ("29ce1577d5dc8322", "6dcb3071f9d4ff4f", "e2ea641e63a75d2a", "e8cb4719ff4c234d"),
}

def rowhash(values):
    return hashlib.sha256("".join(f"{x}\n" for x in values).encode("ascii")).hexdigest()[:16]

def load(tag, setname):
    with open(f"{ROWS}/{tag}_{setname}_d12.json") as f:
        d = json.load(f)
    return d["per_position"], d["bestmove"]

def main():
    ok = True
    data = {}
    for tag in ("base", "ident", "nt3", "nc2", "mc1", "sf"):
        for s in ("O", "G"):
            data[(tag, s)] = load(tag, s)
    print("== hash check against file 22 known rows ==")
    for tag, (on, om, gn, gm) in KNOWN.items():
        for s, kn, km in (("O", on, om), ("G", gn, gm)):
            nodes, bms = data[(tag, s)]
            hn, hm = rowhash(nodes), rowhash(bms)
            stat = "OK " if (hn, hm) == (kn, km) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:5s} {s}  n {hn} (want {kn})  m {hm} (want {km})  n_pos={len(nodes)}")
    print("== identity: ident vs base per position ==")
    for s in ("O", "G"):
        bn, bb = data[("base", s)]
        in_, ib = data[("ident", s)]
        eq_n = sum(1 for a, b in zip(bn, in_) if a == b)
        eq_b = sum(1 for a, b in zip(bb, ib) if a == b)
        print(f"{s}: nodes equal {eq_n}/{len(bn)}, best moves equal {eq_b}/{len(bb)}")
        if eq_n != len(bn) or eq_b != len(bb):
            ok = False
    print("== positions where the ON setting changes the node count vs base ==")
    for tag in ("nt3", "nc2", "mc1", "sf"):
        for s in ("O", "G"):
            bn, bb = data[("base", s)]
            tn, tb = data[(tag, s)]
            ch_n = sum(1 for a, b in zip(bn, tn) if a != b)
            ch_b = sum(1 for a, b in zip(bb, tb) if a != b)
            print(f"{tag:4s} {s}: nodes changed {ch_n}/{len(bn)}, best moves changed {ch_b}/{len(bb)}")
    print("RESULT:", "ALL EQUAL" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
