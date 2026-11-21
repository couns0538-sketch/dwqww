#!/usr/bin/env bash
# kimi5 job 40 step 3 driver: runs runlist.tsv (option<TAB>value<TAB>set) through the
# capped harness, 4 parallel processes (= core count), table order, O before G.
# Usage: run_s3.sh <patched_exe>   (run from the forge-combo29 dir)
set -u
EXE="$1"
J=tests_kimi5_job40
PIDS=()
while IFS=$'\t' read -r name value set; do
  [ -z "$name" ] && continue
  vtag=$(echo "$value" | sed 's/-/m/')
  tag="s3_${name}_${vtag}_${set}"
  base="kimi5/job37/k3/base${set}.rows"
  epd="kimi5/job39/${set}.epd"
  python3 "$J/runner_j40.py" "$EXE" "$epd" "$J/s3" "$tag" --cap "$base" 10/1 -- "$J/opt/opt_${name}_${vtag}.txt" > "$J/s3/${tag}.log" 2>&1 &
  PIDS+=($!)
  while [ "$(jobs -rp | wc -l)" -ge 4 ]; do sleep 1; done
done < "$J/runlist.tsv"
wait
echo "all step 3 runs finished"
