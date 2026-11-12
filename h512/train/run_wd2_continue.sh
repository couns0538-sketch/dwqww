#!/usr/bin/env bash
# JOB E phase 2: after the second-round arms X1..X5, continue the best arm whose 2.0B stage-end selection loss is at
# least 2e-5 below W2's 0.014083 (addendum 6), with plan h512/train/plans/wd2c_<arm>.json. If none qualifies, nothing
# is run. The choice is written to _work/runs/arms/WINNER_ROUND2.txt.
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
win=$("$PY" -I -B - <<'PY'
import json
D = "D:/forge_jobs_20261111/h512E/_work/runs/arms"
vals = {}
for arm in ("X1", "X2", "X3", "X4", "X5"):
    last = None
    try:
        for line in open(f"{D}/wd2_{arm}/metrics.jsonl", encoding="utf-8"):
            e = json.loads(line)
            if e["stage"] == "S2" and e["stage_end"]:
                last = e["metric"]
    except OSError:
        pass
    vals[arm] = last
bar = 0.014083169095418995 - 2e-5
good = {a: v for a, v in vals.items() if v is not None and v <= bar}
print((min(good, key=good.get) if good else "NONE") + " " + json.dumps(vals))
PY
)
echo "$(date '+%F %T') $win" >> "$D/_work/runs/arms/WINNER_ROUND2.txt"
arm="${win%% *}"
[ "$arm" = "NONE" ] && exit 0
bash "$D/h512/train/run_arm.sh" "wd2c_$arm" "$D/_work/runs/arms/wd2_$arm/stage_S2.pt"
