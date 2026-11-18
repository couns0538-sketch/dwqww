#!/usr/bin/env python3
"""kimi5 job 23 Step 1 checker: per-position equality against file 23's known row hashes,
the i2/i3 identities, and per-ON-setting changed-position counts.
Row hash (file 22 head, reused by file 23): first 16 hex of sha256 of the values in
position order, each followed by one LF. Usage: check_s1_j23.py <rows_dir>"""
import hashlib
import json
import sys

ROWS = sys.argv[1] if len(sys.argv) > 1 else "rows"

KNOWN = {
    # tag: (O_n, O_m, G_n, G_m)  from FABLE_TO_kimi5_23.md
    "base": ("fd609b7b1a8dd179", "14583c86b5f56cb6", "60b6916f01395e99", "0846f027e7e9b77e"),
    "fh":   ("6d6a7e91d5a78640", "0e6d255acdeceb2d", "56ce54b4b46f7652", "0d805736a4c5a2f5"),
    "fhr":  ("615a960d245aea19", "bd74b113c4abe155", "d35a428bc64db907", "14e6e9ea5a2a802f"),
    "cn":   ("9af9e9043c9941e9", "cc9fcdd7255f2611", "7db85736e120b87a", "591e2b8f7af4df22"),
}

SUMS = {
    # tag: (O_sum, O_first3, G_sum, G_first3)
    "base": (8315168, (21812, 26844, 35173), 17611204, (31779, 46086, 84457)),
    "fh":   (9869613, (22929, 28167, 38486), 20708347, (45412, 81149, 83115)),
    "fhr":  (8603740, (18239, 20201, 33740), 18522408, (36172, 36206, 46941)),
    "cn":   (8443473, (21882, 22404, 41424), 16949824, (40008, 45546, 67388)),
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
    for tag in ("base", "i2", "i3", "fh", "fhr", "cn"):
        for s in ("O", "G"):
            data[(tag, s)] = load(tag, s)
    print("== sums and first-three against file 23 known answers ==")
    for tag, (osum, of3, gsum, gf3) in SUMS.items():
        for s, wsum, wf3 in (("O", osum, of3), ("G", gsum, gf3)):
            nodes, _ = data[(tag, s)]
            stat = "OK " if (sum(nodes), tuple(nodes[:3])) == (wsum, wf3) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}: sum {sum(nodes)} (want {wsum}), first3 {nodes[:3]} (want {list(wf3)})")
    print("== hash check against file 23 known rows ==")
    for tag, (on, om, gn, gm) in KNOWN.items():
        for s, kn, km in (("O", on, om), ("G", gn, gm)):
            nodes, bms = data[(tag, s)]
            hn, hm = rowhash(nodes), rowhash(bms)
            stat = "OK " if (hn, hm) == (kn, km) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}  n {hn} (want {kn})  m {hm} (want {km})  n_pos={len(nodes)}")
    print("== identities: i2 and i3 vs base per position ==")
    for tag in ("i2", "i3"):
        for s in ("O", "G"):
            bn, bb = data[("base", s)]
            tn, tb = data[(tag, s)]
            eq_n = sum(1 for a, b in zip(bn, tn) if a == b)
            eq_b = sum(1 for a, b in zip(bb, tb) if a == b)
            print(f"{tag} {s}: nodes equal {eq_n}/{len(bn)}, best moves equal {eq_b}/{len(bb)}")
            if eq_n != len(bn) or eq_b != len(bb):
                ok = False
    print("== positions where the ON setting changes the node count vs base ==")
    for tag in ("i2", "i3", "fh", "fhr", "cn"):
        for s in ("O", "G"):
            bn, bb = data[("base", s)]
            tn, tb = data[(tag, s)]
            ch_n = sum(1 for a, b in zip(bn, tn) if a != b)
            ch_b = sum(1 for a, b in zip(bb, tb) if a != b)
            print(f"{tag:4s} {s}: nodes changed {ch_n}/{len(bn)}, best moves changed {ch_b}/{len(bb)}")
    print("OVERALL:", "ALL EQUAL" if ok else "DIFFERENCES PRESENT")

if __name__ == "__main__":
    main()
