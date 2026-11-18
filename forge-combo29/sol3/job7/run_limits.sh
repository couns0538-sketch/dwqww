#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job7
job=forge-combo29/sol3/job7
positions=forge-combo29/sol3/job3/positions.txt
net=/workspace/work/sol3-job4-net/net768.fnn3
cutoff=$(date -u -d 2026-11-18T12:08:53Z +%s)

save() {
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "$1"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
}

run_one() {
  local limit=$1 cell=$2 arm=$3 out=$4
  local exe=/workspace/work/sol3-job5/build_${arm}f/forge
  local args=("$exe" "$positions" "$out" "$arm" "$cell" --nodes "$limit")
  if [ "$cell" = N2 ]; then args+=(--net "$net"); fi
  local remaining=$((cutoff - $(date -u +%s)))
  local status=0
  {
    printf 'python3 -B %q' "$job/identity.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    sha256sum "$exe" "$positions"
    date -u +%FT%TZ
    if ((remaining > 0)); then
      timeout --kill-after=5s "$remaining" python3 -B "$job/identity.py" "${args[@]}" || status=$?
    else
      status=124
    fi
    printf 'exit_code %s\n' "$status"
    date -u +%FT%TZ
  } > "$out/run_${arm}_${cell}.meta" 2> "$out/run_${arm}_${cell}.stderr.txt"
  return "$status"
}

for limit in 50000 250000; do
  out="$root/$limit"
  mkdir "$out" "$job/$limit"
  for cell in B2 N2; do
    results=0
    children=()
    for arm in 10 11 P; do
      run_one "$limit" "$cell" "$arm" "$out" &
      children+=("$!")
    done
    for pid in "${children[@]}"; do
      wait "$pid" || results=$?
    done
    if [ "$results" -eq 0 ]; then
      python3 -B "$job/compare_limits.py" "$limit" "$root" "$positions" --cell "$cell" > "$out/readback_${cell}.txt" 2> "$out/readback_${cell}.stderr.txt" || results=$?
      cat "$out/readback_${cell}.txt" "$out/readback_${cell}.stderr.txt"
    fi
    cp "$out/"* "$job/$limit/"
    date -u "+%Y-%m-%dT%H:%M:%SZ Step 1 $limit/$cell three arms and raw readback completed, exit $results" >> "$job/stamps.txt"
    save "sol3 job 7 step 1 checkpoint $limit $cell"
    if [ "$results" -ne 0 ]; then
      printf '%s %s STOP (exit %s)\n' "$limit" "$cell" "$results"
      break
    fi
  done
done
