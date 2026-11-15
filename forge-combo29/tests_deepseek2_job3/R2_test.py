#!/usr/bin/env python3
"""Job 3 R2 test: `eval` and the search must name the same evaluator.

This runs the job-2 part A sweep (tests_deepseek2_job2/partA_fingerprint.py,
unchanged) against the given engine and requires:

  * 0 INCONSISTENT among the combinations that survive, and
  * the three controls still land where they must: all defaults and
    `NNUEArch true` + file are consistent; `UseNNUE false` + `NNUEArch true`
    must now ALSO be consistent, because R2 makes `eval` report HCE there.

Exit code 0 when both hold.
"""

import json
import subprocess
import sys

ENGINE = sys.argv[1]
POSFILE = sys.argv[2]
NET = sys.argv[3]
OUT = sys.argv[4]
SWEEP = "/agent/repos/dwqww/forge-combo29/tests_deepseek2_job2/partA_fingerprint.py"

CONTROLS = {
    "UseNNUE=true NNUEArch=false file=unset DeadMaterial=false OwnBook=false MultiPV=1 Threads=1":
        "consistent",
    "UseNNUE=true NNUEArch=true file=set DeadMaterial=false OwnBook=false MultiPV=1 Threads=1":
        "consistent",
    "UseNNUE=false NNUEArch=true file=set DeadMaterial=false OwnBook=false MultiPV=1 Threads=1":
        "consistent",
}


def main():
    raw = OUT.replace(".json", "_sweep.json")
    r = subprocess.run([sys.executable, SWEEP, ENGINE, POSFILE, NET, raw],
                       capture_output=True, text=True)
    print(r.stdout[-2000:])
    if r.returncode != 0:
        print("sweep failed:", r.stderr[-2000:])
        sys.exit(2)
    d = json.load(open(raw))
    res = d["results"]
    counts = {}
    for x in res:
        counts[x["verdict"]] = counts.get(x["verdict"], 0) + 1
    print("verdicts:", counts)
    bad = 0
    if counts.get("INCONSISTENT", 0) != 0:
        print(f"FAIL: {counts['INCONSISTENT']} inconsistent combinations")
        bad += 1
    if counts.get("UNIDENTIFIED", 0) != 0:
        print(f"FAIL: {counts['UNIDENTIFIED']} unidentified combinations")
        bad += 1
    for key, want in CONTROLS.items():
        row = [x for x in res if x["key"] == key]
        if not row:
            print("FAIL: control missing from the sweep:", key)
            bad += 1
            continue
        got = row[0]["verdict"]
        ok = got == want
        print(f"{'ok  ' if ok else 'FAIL'} control {got:14s} (want {want}) {key}")
        if not ok:
            bad += 1
    json.dump({"counts": counts, "controls": {
        k: ([x for x in res if x["key"] == k][0]["verdict"] if [x for x in res if x["key"] == k] else None)
        for k in CONTROLS}}, open(OUT, "w"), indent=1)
    print("R2:", "PASS" if bad == 0 else f"FAIL ({bad} problems)")
    sys.exit(0 if bad == 0 else 1)


if __name__ == "__main__":
    main()
