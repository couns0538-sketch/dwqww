#!/usr/bin/env bash
set -euo pipefail
work=/workspace/work/sol3-job8
job=forge-combo29/sol3/job8
step="$job/step3"
fixture=forge-combo29/sol3/job3/positions.txt
baseline=forge-combo29/sol3/job7
net=/workspace/work/sol3-job4-net/net768.fnn3
remaining=$(date -u -d 2026-11-18T12:29:43Z +%s)
step_status=0
for cell in B2 N2; do
  status=0
  out="$step/$cell"
  mkdir "$out"
  args=("$work/build_vf/forge" "$fixture" "$out" 11 "$cell" --nodes 50000)
  if [ "$cell" = N2 ]; then args+=(--net "$net"); fi
  {
    printf 'python3 -B %q' "$work/identity.py"
    printf ' %q' "${args[@]}"
    printf '\n'
    sha256sum "$work/build_vf/forge" "$work/identity.py" "$fixture"
    if [ "$cell" = N2 ]; then sha256sum "$net"; fi
    date -u +%FT%TZ
  } > "$out/run.meta"
  left=$((remaining - $(date -u +%s)))
  if ((left > 0)); then
    timeout --kill-after=5s "$left" python3 -B "$work/identity.py" "${args[@]}" > "$out/driver.stdout.txt" 2> "$out/driver.stderr.txt" || status=$?
  else
    status=124
  fi
  if ((status == 0)); then
    PYTHONPATH="$work" python3 -B "$step/check_cold.py" "$fixture" "$baseline" "$out" "$cell" > "$out/gate.txt" 2> "$out/gate.stderr.txt" || status=$?
  fi
  date -u "+%FT%TZ Step 3 $cell k11vf 50000 node labels and independent readback exit $status" >> "$job/stamps.txt"
  git add --sparse -- "$step" "$job/stamps.txt"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git commit -qm "sol3 job 8 step 3 checkpoint $cell 50000 node labels"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if test -f "$out/gate.txt"; then cat "$out/gate.txt" "$out/gate.stderr.txt"; fi
  if [ "$status" -ne 0 ]; then step_status=$status; fi
done
test "$step_status" -eq 0
