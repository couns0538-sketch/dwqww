#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job19
work=/workspace/work/sol3-job19
net=/workspace/work/sol3-job4-net/net768.fnn3
fixture="$job/positions.txt"
r15=/workspace/work/sol3-job4/build_0/forge
kf=/workspace/work/sol3-job12/build_F/forge
kf0="$work/build_F0/forge"
kfs="$work/build_Fscalar/forge"
sha0=$(awk 'NR==1 {print $1}' "$job/stage0b/build.sha256")
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
test "$(git log -1 --format=%s -- "$job/prediction.md")" = 'sol3 job 19 prediction'
rg -Fxq 'exit_code 0' "$job/stage0b/gate.txt"

timed() {
  local remaining
  remaining=$((cutoff - $(date -u +%s)))
  if ((remaining <= 0)); then return 124; fi
  timeout --kill-after=5s "$remaining" "$@"
}

checkpoint() {
  local step=$1
  local code=$2
  printf '%s %s exit %s\n' "$(date -u +%FT%TZ)" "$step" "$code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 19 $step"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

w13() {
  local directory=$1
  local workload=$2
  local label=$3
  local binary=$4
  shift 4
  local code=0
  mkdir -p "$job/$directory"
  timed python3 -B "$job/w13.py" run --workload "$workload" --build "$label" --engine "$binary" \
    --net "$net" --fixture "$fixture" --output "$job/$directory/$label" --timeout 60 "$@" \
    > "$job/$directory/$label.driver.stdout.txt" 2> "$job/$directory/$label.driver.stderr.txt" || code=$?
  checkpoint "$directory $label raw run" "$code"
  if ((code != 0)); then cat "$job/$directory/$label.driver.stderr.txt"; fi
  return "$code"
}

compare_w13() {
  local directory=$1
  local left=$2
  local right=$3
  local code=0
  python3 -B "$job/w13.py" compare "$job/$directory/$left" "$job/$directory/$right" --fixture "$fixture" \
    > "$job/$directory/comparison.json" 2> "$job/$directory/compare.stderr.txt" || code=$?
  checkpoint "$directory readback compared $left versus $right" "$code"
  if [[ ! -s "$job/$directory/comparison.json" ]]; then cat "$job/$directory/compare.stderr.txt"; fi
}

w13 W1 W1 r15d "$r15"
w13 W1 W1 kF "$kf"
compare_w13 W1 r15d kF

mkdir -p "$job/W2"
for label in r15d kF; do
  if [[ $label == r15d ]]; then binary=$r15; else binary=$kf; fi
  code=0
  timed python3 -B "$job/run_w2.py" "$binary" "$fixture" "$net" "$job/W2/$label" \
    > "$job/W2/$label.driver.stdout.txt" 2> "$job/W2/$label.driver.stderr.txt" || code=$?
  checkpoint "W2 $label warm sequence and fresh process controls" "$code"
  if ((code != 0)); then cat "$job/W2/$label.driver.stderr.txt"; exit "$code"; fi
done
code=0
python3 -B "$job/compare_w2.py" "$fixture" "$net" "$job/W2/r15d" "$job/W2/kF" \
  > "$job/W2/comparison.json" 2> "$job/W2/compare.stderr.txt" || code=$?
checkpoint 'W2 stable line and fresh controls readback' "$code"
if ((code != 0)); then cat "$job/W2/compare.stderr.txt"; fi

w13 W3_depth W3-depth kF "$kf"
w13 W3_depth W3-depth kF0 "$kf0" --exe-sha256 "$sha0"
compare_w13 W3_depth kF kF0
w13 W3_eval W3-eval kF "$kf"
w13 W3_eval W3-eval kF0 "$kf0" --exe-sha256 "$sha0"
compare_w13 W3_eval kF kF0

mkdir -p "$job/scalar"
cp "$work"/{build_scalar.py,build_scalar.txt,kF_nnue_v3_compile_line.txt} "$job/scalar/"
code=0
timed python3 -B "$job/pins19.py" "$kfs" "$job/scalar/pins" "$net" --net-only \
  > "$job/scalar/pins.stdout.txt" 2> "$job/scalar/pins.stderr.txt" || code=$?
checkpoint 'supplemental scalar v3 executable and active-net pins' "$code"
if ((code == 0)); then
  w13 scalar W3-depth kFscalar "$kfs" --exe-sha256 "$(sha256sum "$kfs" | cut -d' ' -f1)"
  code=0
  python3 -B "$job/w13.py" compare "$job/W3_depth/kF" "$job/scalar/kFscalar" --fixture "$fixture" \
    > "$job/scalar/comparison.json" 2> "$job/scalar/compare.stderr.txt" || code=$?
  checkpoint 'supplemental compare actual AVX-512 and scalar v3 searches' "$code"
else
  cat "$job/scalar/pins.stderr.txt"
fi
