#!/usr/bin/env python3
"""kimi5 job 25 step 3: aggregate the A25C counter lines over ALL searches of the
counting build's runs, and check the two closures and the node identity against
Step 1's rows (the first known answer). Prints how many lines it summed.
Run from tests_kimi5_job25/.
"""
import glob, json, sys

SLOT = ["tests", "ext1", "ext2", "mcut", "extm2", "extm1", "none",
        "ttLow", "ttUpp", "ttExa", "rfpRet", "rfRet", "rfNoPv", "rfTtGd", "rfCorr", "rfToday"]

ok = True
grand = {}
for path in sorted(glob.glob("rows_count/*_d12_full.txt")):
    tag = path.split("/")[-1].replace("_d12_full.txt", "")
    lines = 0
    tot = [0] * 16
    with open(path) as f:
        for line in f:
            if line.startswith("A25C"):
                parts = line.split()
                assert len(parts) == 17, f"bad A25C line in {path}: {line!r}"
                for i in range(16):
                    tot[i] += int(parts[1 + i])
                lines += 1
    grand[tag] = (lines, tot)
    c1 = tot[0] == sum(tot[1:7])
    c2 = tot[15] == sum(tot[11:15])
    if not (c1 and c2):
        ok = False
    print(f"{tag:12s} searches={lines:4d} " + " ".join(f"{SLOT[i]}={tot[i]}" for i in range(16))
          + f"  closureSNG={'OK' if c1 else 'BAD'} closureRFP={'OK' if c2 else 'BAD'}")

print()
print("== node identity: counting build rows vs Step 1 plain rows (first known answer) ==")
for tag in ("base", "fhb1", "fhb2", "fhb4", "fhb7", "rfp3"):
    for st in ("O", "G"):
        with open(f"rows_count/{tag}_{st}_d12.json") as f:
            a = json.load(f)
        with open(f"rows/{tag}_{st}_d12.json") as f:
            b = json.load(f)
        same = a["per_position"] == b["per_position"] and a["bestmove"] == b["bestmove"]
        if not same:
            ok = False
        print(f"{tag:5s} {st}: {'EQUAL' if same else 'DIFF'} (sum {sum(a['per_position'])} vs {sum(b['per_position'])})")

nfiles = len(glob.glob("rows_count/*_d12_full.txt"))
print(f"\nsummed {nfiles} full-output files")
sys.exit(0 if ok else 1)
