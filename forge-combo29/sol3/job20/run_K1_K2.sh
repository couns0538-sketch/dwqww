#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job20
prior=forge-combo29/sol3/job19
work=/workspace/work/sol3-job20
source=/workspace/work/sol3-job20-shadow
for arm in r15d kF; do
  bash "$job/run_depth.sh" K1 "$arm-shadow" "$work/build_$arm/forge" shadow 9 "$prior/positions.txt" --baseline "$prior/W1/$arm"
  python3 - "$job/K1/$arm-shadow/summary.json" <<'PY'
import json
from pathlib import Path
import sys
data=json.loads(Path(sys.argv[1]).read_text())
print({k:data[k] for k in ('build','terminal_nodes','shadow_evals','shadow_differ','reference')})
assert data['terminal_nodes']==16543291
assert data['reference']['equal']==1000 and data['reference']['differ']==0
PY
done
cp "$source"/{promotion_control.patch.txt,plant_apply.txt,plant_diff_receipt.txt} "$job/"
cp "$work/build_plant.txt" "$job/build/"
sha256sum "$work/build_plant/forge" > "$job/build/promotion_control_executable.sha256.txt"
printf '%s %s\n' "$(date -u +%FT%TZ)" 'Step 2 K1 passed; K2 separate one-line promotion plant frozen and rebuilt' >> "$job/stamps.txt"
git add -- "$job"
git commit -m 'sol3 job 20 step 2 freeze separate promotion fault control'
bash /workspace/work/sol3-job3/push-checkpoint.sh
bash "$job/run_depth.sh" K2 kF-promotion-control "$work/build_plant/forge" shadow 9 "$prior/positions.txt" --limit 200
python3 - "$job/K2/kF-promotion-control/summary.json" <<'PY'
import json
from pathlib import Path
import sys
data=json.loads(Path(sys.argv[1]).read_text())
print({k:data[k] for k in ('build','terminal_nodes','shadow_evals','shadow_differ','first_differences')})
assert data['shadow_differ']>0 and data['first_differences']
PY
printf '%s %s\n' "$(date -u +%FT%TZ)" 'Step 2 K1 exact gate and K2 detection gate passed' >> "$job/stamps.txt"
git add -- "$job/stamps.txt"
git commit -m 'sol3 job 20 step 2 checkpoint known identities and fault detection pass'
bash /workspace/work/sol3-job3/push-checkpoint.sh
