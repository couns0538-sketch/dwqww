#!/usr/bin/env bash
# JOB E phase 2: after the weight-decay pilot arms W1..W3 have finished, continue the winner (the lowest selection
# loss at the 2.0B stage end, and at least 2e-5 below both phase-1 S2's 0.014481 and the control arm W0) with its plan
# h512/train/plans/wdc_<arm>.json. If no arm helps, nothing is run. The choice is written to _work/runs/wd/WINNER.txt.
set -u
D=/d/forge_jobs_20261111/h512E; source "$D/h512/train/env_h512.sh"
while ! grep -q 'wd queue finished' "$D/_work/runs/wd/queue.log"; do sleep 10; done
win=$("$PY" -I -B - <<'PY'
import json
D = "D:/forge_jobs_20261111/h512E/_work/runs/wd"
def end(arm):
    last = None
    for line in open(f"{D}/{arm}/metrics.jsonl", encoding="utf-8"):
        e = json.loads(line)
        if e["stage"] == "S2" and e["stage_end"]:
            last = e["metric"]
    return last
vals = {}
for arm in ("W0", "W1", "W2", "W3"):
    try:
        vals[arm] = end(arm)
    except OSError:
        vals[arm] = None
bar = min(0.014481, vals["W0"]) - 2e-5
good = {a: v for a, v in vals.items() if a != "W0" and v is not None and v <= bar}
print((min(good, key=good.get) if good else "NONE") + " " + json.dumps(vals))
PY
)
echo "$(date '+%F %T') $win" >> "$D/_work/runs/wd/WINNER.txt"
arm="${win%% *}"
[ "$arm" = "NONE" ] && exit 0
bash "$D/h512/train/run_arm.sh" "wdc_$arm" "$D/_work/runs/wd/$arm/stage_S2.pt"
