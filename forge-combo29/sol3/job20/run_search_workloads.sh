#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job20
prior=forge-combo29/sol3/job19
work=/workspace/work/sol3-job20
net=/workspace/work/sol3-job4-net/net768.fnn3
fixture="$prior/positions.txt"
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 20 prediction'
rg -Fq 'Step 2 K1 exact gate and K2 detection gate passed' "$job/stamps.txt"

checkpoint() {
  local step=$1
  local code=$2
  printf '%s %s exit %s\n' "$(date -u +%FT%TZ)" "$step" "$code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 20 $step"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}
for arm in r15d kF; do
  bash "$job/run_depth.sh" S1 "$arm-shadow" "$work/build_$arm/forge" shadow 9 "$fixture" --baseline "$prior/W1/$arm"
done

mkdir -p "$job/S2"
for arm in r15d kF; do
  remaining=$((cutoff - $(date -u +%s)))
  status=0
  binary="$work/build_$arm/forge"
  sha=$(sha256sum "$binary" | cut -d' ' -f1)
  args=(python3 -B "$job/s2_games.py" run --engine "$binary" --exe-sha256 "$sha"
        --build "$arm-shadow" --net "$net" --fixture "$fixture" --output "$job/S2/$arm-shadow")
  {
    printf 'PYTHONPATH=%q ' /workspace/work/sol3-replay/python
    printf '%q ' "${args[@]}"
    printf '\n'
  } > "$job/S2/$arm-shadow.command.txt"
  if ((remaining > 0)); then
    PYTHONPATH=/workspace/work/sol3-replay/python timeout --kill-after=5s "$remaining" "${args[@]}" \
      > "$job/S2/$arm-shadow.driver.stdout.txt" 2> "$job/S2/$arm-shadow.driver.stderr.txt" || status=$?
  else
    status=124
  fi
  checkpoint "S2 $arm-shadow game paths" "$status"
  if ((status != 0)); then cat "$job/S2/$arm-shadow.driver.stderr.txt"; exit "$status"; fi
done
status=0
PYTHONPATH=/workspace/work/sol3-replay/python python3 -B "$job/s2_check.py" compare --fixture "$fixture" \
  "$job/S2/r15d-shadow" "$job/S2/kF-shadow" > "$job/S2/comparison.json" 2> "$job/S2/compare.stderr.txt" || status=$?
checkpoint 'S2 independent raw legal replay and comparison' "$status"
if ((status != 0)); then cat "$job/S2/compare.stderr.txt"; fi

if (($(date -u +%s) >= cutoff)); then exit 0; fi
kf=/workspace/work/sol3-job12/build_F/forge
kfs=/workspace/work/sol3-job19/build_Fscalar/forge
bash "$job/run_depth.sh" S3_W1 kF "$kf" plain 9 "$fixture" --baseline "$prior/W1/kF"
bash "$job/run_depth.sh" S3_W1 kFscalar "$kfs" plain 9 "$fixture" --baseline "$prior/W1/kF"
status=0
python3 -B "$job/shadow_depth.py" compare "$job/S3_W1/kF" "$job/S3_W1/kFscalar" --fixture "$fixture" --depth 9 \
  > "$job/S3_W1/comparison.json" 2> "$job/S3_W1/compare.stderr.txt" || status=$?
checkpoint 'S3 all 1000 AVX512 vs scalar net searches readback' "$status"
if ((status != 0)); then cat "$job/S3_W1/compare.stderr.txt"; fi
if (($(date -u +%s) >= cutoff)); then exit 0; fi
bash "$job/run_depth.sh" S3_O kFscalar "$kfs" plain 12 "$work/O200.fen.txt"
python3 - "$job/S3_O/kFscalar/summary.json" <<'PY'
import json
from pathlib import Path
import sys
data=json.loads(Path(sys.argv[1]).read_text())
print({k:data[k] for k in ('build','terminal_nodes','first_three_nodes')})
PY
