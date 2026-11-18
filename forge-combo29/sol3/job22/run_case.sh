#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job22
fixture=forge-combo29/sol3/job19/positions.txt
net=/workspace/work/sol3-job4-net/net768.fnn3
engine=$1
part=$2
label=$3
phase=$4
shift 4
dir="$job/$phase"
mkdir -p "$dir"
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
remaining=$((cutoff - $(date -u +%s)))
exe_sha=$(sha256sum "$engine" | cut -d' ' -f1)
args=(python3 -B "$job/sanitizer_uci.py" --part "$part" --engine "$engine"
      --exe-sha256 "$exe_sha" --label "$label" --net "$net" --fixture "$fixture"
      --output "$dir/$label" --timeout 120 "$@")
{
  cat "$job/sanitizer.env.txt"
  if [[ "$label" == C-T-pos-* ]]; then printf '%s\n' 'TSAN_OPTIONS=halt_on_error=1:exitcode=66'; fi
  printf 'PYTHONPATH=%q ' /workspace/work/sol3-replay/python
  printf '%q ' "${args[@]}"
  printf '\n'
} > "$dir/$label.invocation.txt"
code=0
if ((remaining > 0)); then
  (
    set -a
    source "$job/sanitizer.env.txt"
    set +a
    if [[ "$label" == C-T-pos-* ]]; then export TSAN_OPTIONS=halt_on_error=1:exitcode=66; fi
    PYTHONPATH=/workspace/work/sol3-replay/python timeout --kill-after=3s "$remaining" "${args[@]}"
  ) > "$dir/$label.driver.stdout.txt" 2> "$dir/$label.driver.stderr.txt" || code=$?
else
  code=124
fi
printf '%s %s %s harness exit %s\n' "$(date -u +%FT%TZ)" "$phase" "$label" "$code" >> "$job/stamps.txt"
git add -- "$job"
git commit -m "sol3 job 22 $phase retain $label full sanitizer streams"
bash /workspace/work/sol3-job3/push-checkpoint.sh
if [[ -s "$dir/$label.driver.stderr.txt" ]]; then head -12 "$dir/$label.driver.stderr.txt"; fi
exit "$code"
