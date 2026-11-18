#!/usr/bin/env python3
"""kimi5 job 24 Step 1 checker: per-position equality against file 24's known row hashes
and sums, plus per-ON-setting changed-position counts against base.
Row hash (file 22 head, reused by file 24): first 16 hex of sha256 of the values in
position order, each followed by one LF. Usage: check_s1_j24.py <rows_dir> [depth]"""
import hashlib
import json
import sys

ROWS = sys.argv[1] if len(sys.argv) > 1 else "rows"
DEPTH = sys.argv[2] if len(sys.argv) > 2 else "12"

KNOWN = {
    # tag: (O_n, O_m, G_n, G_m)  from FABLE_TO_kimi5_24.md
    "base": ("fd609b7b1a8dd179", "14583c86b5f56cb6", "60b6916f01395e99", "0846f027e7e9b77e"),
    "nc":   ("f639f36890befbbf", "c0b2d98b159a038f", "c8b46d53fdeee08c", "4a884189aa8f6ed7"),
    "t5":   ("b263538bf49b04ba", "e7df4079c2e4b714", "e0d52e21d2231430", "0a14046c7ba38f3a"),
    "both": ("a696c2ba1bcc7985", "af9821530a1e8878", "867a41f0acaec819", "77d7a4196127e6b5"),
}

SUMS = {
    # tag: (O_sum, O_first3, G_sum, G_first3)
    "base": (8315168, (21812, 26844, 35173), 17611204, (31779, 46086, 84457)),
    "nc":   (8274914, (21808, 24169, 36223), 18015717, (51019, 46063, 69969)),
    "t5":   (8658881, (19509, 14230, 31329), 17596929, (39862, 39527, 51676)),
    "both": (8590222, (19507, 14230, 30592), 17955756, (54255, 39512, 70659)),
}

def rowhash(values):
    return hashlib.sha256("".join(f"{x}\n" for x in values).encode("ascii")).hexdigest()[:16]

def load(tag, setname):
    with open(f"{ROWS}/{tag}_{setname}_d{DEPTH}.json") as f:
        d = json.load(f)
    return d["per_position"], d["bestmove"]

def main():
    ok = True
    data = {}
    for tag in ("base", "nc", "t5", "both"):
        for s in ("O", "G"):
            data[(tag, s)] = load(tag, s)
    print(f"== sums and first-three against file 24 known answers (depth {DEPTH}) ==")
    for tag, (osum, of3, gsum, gf3) in SUMS.items():
        for s, wsum, wf3 in (("O", osum, of3), ("G", gsum, gf3)):
            nodes, _ = data[(tag, s)]
            stat = "OK " if (sum(nodes), tuple(nodes[:3])) == (wsum, wf3) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}: sum {sum(nodes)} (want {wsum}), first3 {nodes[:3]} (want {list(wf3)})")
    print("== hash check against file 24 known rows ==")
    for tag, (on, om, gn, gm) in KNOWN.items():
        for s, kn, km in (("O", on, om), ("G", gn, gm)):
            nodes, bms = data[(tag, s)]
            hn, hm = rowhash(nodes), rowhash(bms)
            stat = "OK " if (hn, hm) == (kn, km) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}  n {hn} (want {kn})  m {hm} (want {km})  n_pos={len(nodes)}")
    print("== changed node counts per ON setting against base ==")
    for tag in ("nc", "t5", "both"):
        for s in ("O", "G"):
            bn, bb = data[("base", s)]
            tn, tb = data[(tag, s)]
            cn = sum(1 for a, b in zip(bn, tn) if a != b)
            cb = sum(1 for a, b in zip(bb, tb) if a != b)
            ident = "IDENTICAL" if cn == 0 and cb == 0 else f"nodes differ on {cn}/{len(bn)}, bestmove on {cb}/{len(bb)}"
            print(f"{tag:4s} {s}: {ident}")
    print("OVERALL:", "ALL EQUAL" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
