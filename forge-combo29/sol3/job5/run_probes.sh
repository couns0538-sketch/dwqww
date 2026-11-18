#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job5
job=forge-combo29/sol3/job5
prev=/workspace/work/sol3-job4
ref_job=forge-combo29/sol3/job4
positions=forge-combo29/sol3/job3/positions.txt
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T10:32:59Z +%s)

save() {
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "$1"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

for arm in 10 11 P; do
  tree="$root/tree_${arm}f"
  build="$root/build_${arm}f"
  evidence="$root/step4/build_${arm}f"
  mkdir -p "$tree" "$evidence"
  cp -a "$prev/tree_$arm/." "$tree/"
  patch_file="$job/probe.diff"
  if [ "$arm" = 10 ]; then
    patch_file="$root/probe_k10.line-adjusted.diff"
    sed 's/^@@ -3629,6 +3629,17 @@$/@@ -3626,6 +3626,17 @@/' "$job/probe.diff" > "$patch_file"
  fi
  status=0
  {
    printf 'probe patch SHA and hunk\n'
    sha256sum "$patch_file"
    rg '^@@' "$patch_file"
    LC_ALL=C patch -d "$tree" -p1 -F0 --batch --forward -i "$(realpath "$patch_file")" || status=$?
    if rg -qi 'offset|fuzz|FAILED|reject|Skipping|Reversed' "$evidence/patch_${arm}f.txt"; then status=21; fi
    printf 'patch_exit %s\n' "$status"
  } > "$evidence/patch_${arm}f.txt" 2>&1
  remaining=$((cutoff - $(date -u +%s)))
  if [ "$status" -eq 0 ] && (( remaining > 0 )); then
    timeout --kill-after=5s "$remaining" bash /workspace/work/sol3-job3/build_one.sh "$tree" "$build" "$evidence/build_${arm}f.txt" || status=$?
  elif [ "$status" -eq 0 ]; then
    status=124
  fi
  cp "$evidence/"*.txt "$job/"
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 4 probe ${arm}f applied and built, exit $status" >> "$job/stamps.txt"
  save "sol3 job 5 step 4 checkpoint probe build ${arm}f"
  test "$status" -eq 0

  for cell in B2 N2; do
    out="$root/step4/${arm}_$cell"
    mkdir "$out"
    status=0
    args=("$build/forge" "$positions" "$out" "$arm" "$cell")
    if [ "$cell" = N2 ]; then args+=(--net "$net"); fi
    remaining=$((cutoff - $(date -u +%s)))
    {
      date -u +%FT%TZ
      printf 'python3 -B %q' "$ref_job/identity.py"
      printf ' %q' "${args[@]}"
      printf '\n'
      if (( remaining > 0 )); then
        timeout --kill-after=5s "$remaining" python3 -B "$ref_job/identity.py" "${args[@]}" || status=$?
      else
        status=124
      fi
      printf 'exit_code %s\n' "$status"
      date -u +%FT%TZ
    } > "$out/run_${arm}_${cell}.txt" 2> "$out/run_${arm}_${cell}.stderr.txt"
    if [ "$status" -eq 0 ]; then
      cmp "$out/rows_${arm}_${cell}.txt" "$ref_job/rows_11_${cell}.txt" > "$out/rows_${arm}_${cell}.compare.txt" 2>&1 || status=$?
    fi
    cp "$out/"*.txt "$job/"
    date -u "+%Y-%m-%dT%H:%M:%SZ Step 4 ${arm}f/$cell probe and legacy row check exited $status" >> "$job/stamps.txt"
    save "sol3 job 5 step 4 checkpoint ${arm}f $cell"
    test "$status" -eq 0
  done
done
status=0
python3 -B "$job/analyze_probe.py" "$job" "$ref_job" > "$job/probe_readback.txt" 2> "$job/probe_readback.stderr.txt" || status=$?
cat "$job/probe_readback.txt" "$job/probe_readback.stderr.txt"
printf 'exit_code %s\n' "$status" > "$job/probe_status.txt"
date -u "+%Y-%m-%dT%H:%M:%SZ Step 4 completed independent final-count readback and control; exit $status" >> "$job/stamps.txt"
save 'sol3 job 5 step 4 preserve hard-limit probe table and gate'
test "$status" -eq 0
