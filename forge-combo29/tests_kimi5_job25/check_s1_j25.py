#!/usr/bin/env python3
"""kimi5 job 25 Step 1 checker: per-position equality against file 25's known row hashes
and sums, plus per-ON-setting changed-position counts against base.
Row hash (file 22 head, reused by file 25): first 16 hex of sha256 of the values in
position order, each followed by one LF. Usage: check_s1_j25.py <rows_dir> [depth]"""
import hashlib
import json
import sys

ROWS = sys.argv[1] if len(sys.argv) > 1 else "rows"
DEPTH = sys.argv[2] if len(sys.argv) > 2 else "12"

TAGS = ("base", "fhb1", "fhb2", "fhb4", "fhb7", "rfp3", "a2a5")

KNOWN = {
    # tag: (O_n, O_m, G_n, G_m)  from FABLE_TO_kimi5_25.md (base: as in files 18 to 24)
    "base": ("fd609b7b1a8dd179", "14583c86b5f56cb6", "60b6916f01395e99", "0846f027e7e9b77e"),
    "fhb1": ("1a31e4ba254144f0", "9a8f84c5753ed89f", "ab734bd63f73a87a", "80318f709ffd5c45"),
    "fhb2": ("4df7836d75c9b6d6", "7ae97317bdb50de5", "54d5d762cc0323e7", "e5243fee3380361a"),
    "fhb4": ("29f92f07700f13bf", "e9a7fc0ce378d125", "db99424c8f057b32", "1fcbf8eee62fc1ff"),
    "fhb7": ("75509856e2b96287", "1ec0bb858b7ca372", "48255179b3c50754", "6c7dc5dc109bdd8b"),
    "rfp3": ("3be6919a018106df", "e7b85bf3963f6b7e", "545f90f507a61456", "d614ac5c31cf0e0e"),
    "a2a5": ("783275eb7c27c467", "9c0550de43be7989", "6dac75dbb9085162", "52b6f32850bce0e8"),
}

SUMS = {
    # tag: (O_sum, O_first3, G_sum, G_first3)
    "base": (8315168, None, 17611204, None),
    "fhb1": (8047442, (15153, 25717, 30114), 16414051, (28074, 49627, 51046)),
    "fhb2": (8365550, (10615, 25609, 31695), 16615620, (28833, 43854, 56395)),
    "fhb4": (7848675, (13825, 17041, 23353), 16713536, (30492, 49925, 61420)),
    "fhb7": (7913480, (18623, 19820, 32078), 15879039, (30412, 57137, 44902)),
    "rfp3": (8489739, (53405, 23011, 54122), 17980776, (43807, 34242, 39865)),
    "a2a5": (7992289, (19649, 22761, 33543), 16949516, (53133, 40235, 60622)),
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
    for tag in TAGS:
        for s in ("O", "G"):
            data[(tag, s)] = load(tag, s)
    print(f"== sums and first-three against file 25 known answers (depth {DEPTH}) ==")
    for tag, (osum, of3, gsum, gf3) in SUMS.items():
        for s, wsum, wf3 in (("O", osum, of3), ("G", gsum, gf3)):
            nodes, _ = data[(tag, s)]
            want = (wsum, tuple(wf3) if wf3 else None)
            got = (sum(nodes), tuple(nodes[:3]) if wf3 else None)
            stat = "OK " if got == want else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}: sum {got[0]} (want {want[0]}), first3 {nodes[:3]} (want {want[1]})")
    print("== hash check against file 25 known rows ==")
    for tag, (on, om, gn, gm) in KNOWN.items():
        for s, kn, km in (("O", on, om), ("G", gn, gm)):
            nodes, bms = data[(tag, s)]
            hn, hm = rowhash(nodes), rowhash(bms)
            stat = "OK " if (hn, hm) == (kn, km) else "DIFF"
            if stat == "DIFF":
                ok = False
            print(f"{stat} {tag:4s} {s}  n {hn} (want {kn})  m {hm} (want {km})  n_pos={len(nodes)}")
    print("== changed node counts per ON setting against base ==")
    for tag in TAGS[1:]:
        for s in ("O", "G"):
            bn, bm = data[("base", s)]
            tn, tm = data[(tag, s)]
            cn = sum(1 for a, b in zip(bn, tn) if a != b)
            cm = sum(1 for a, b in zip(bm, tm) if a != b)
            print(f"{tag:4s} {s}: nodes changed on {cn} of {len(bn)} positions; best moves changed on {cm}")
    print("== per-position equality vs own port is implied by the hashes above ==")
    sys.exit(0 if ok else 1)

main()
