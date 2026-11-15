#!/bin/bash
# Step 0: known numbers. Fresh engine process per run.
# Options every test depends on stand in every run's input (Threads 1, Hash 16, OwnBook false
# per BUNDLES.md bench box; bundle option appended when the config has one).
ENG=/tmp/g3job1/build/forge
OUT=/tmp/g3job1/step0
mkdir -p "$OUT"

run() {
  local tag="$1" opts="$2" cmd="$3"
  {
    echo uci
    echo "setoption name Threads value 1"
    echo "setoption name Hash value 16"
    echo "setoption name OwnBook value false"
    if [ -n "$opts" ]; then echo "$opts"; fi
    echo isready
    echo "position startpos"
    echo "$cmd"
    echo quit
  } | "$ENG" > "$OUT/$tag.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) step0 $tag done" >> /tmp/g3job1/stamps.txt
}

run off_d11     "" "bench 11"
run off_d13     "" "bench 13"
run off_perft5  "" "go perft 5"
run b1_d11      "setoption name BundlePreset value B1" "bench 11"
run b1_d13      "setoption name BundlePreset value B1" "bench 13"
run b2_d11      "setoption name BundlePreset value B2" "bench 11"
run b2_d13      "setoption name BundlePreset value B2" "bench 13"
run b3_d11      "setoption name BundlePreset value B3" "bench 11"
run b3_d13      "setoption name BundlePreset value B3" "bench 13"
run b4_d11      "setoption name BundlePreset value B4" "bench 11"
run b4_d13      "setoption name BundlePreset value B4" "bench 13"
run corrhv2_d11 "setoption name CorrHistV2 value true" "bench 11"
run corrhv2_d13 "setoption name CorrHistV2 value true" "bench 13"
run lmrv2_d11   "setoption name LmrTableV2 value true" "bench 11"
run lmrv2_d13   "setoption name LmrTableV2 value true" "bench 13"

echo "== extracted nodes =="
for f in "$OUT"/*.out; do
  tag=$(basename "$f" .out)
  n=$(grep -o 'bench depth [0-9]* nodes [0-9]*' "$f" | awk '{print $4}')
  [ -z "$n" ] && n=$(grep -o 'perft .*nodes [0-9]*' "$f" | awk '{print $NF}')
  echo "$tag $n"
done
