#!/usr/bin/env bash
set -euo pipefail
engine=$1
driver=$2
out=$3
shift 3
net=/workspace/work/sol3-job4-net/net768.fnn3
remaining=$(date -u -d "${SOL3_WARM_CUTOFF:-2026-11-18T14:02:20Z}" +%s)
remaining=$((remaining - $(date -u +%s)))
args=(--engine "$engine" --net "$net" --games 60 --softnodes 2000 --random-plies 8 --max-plies 300 --seed 20261117 --json --trace "$out/trace.jsonl" "$@")
{
  printf 'python3 -B %q' "$driver"
  printf ' %q' "${args[@]}"
  printf '\n'
  sha256sum "$engine" "$driver" "$net"
  date -u +%FT%TZ
} > "$out/run.meta"
status=0
if ((remaining > 0)); then
  timeout --kill-after=5s "$remaining" python3 -B "$driver" "${args[@]}" > "$out/summary.json" 2> "$out/driver.stderr.txt" || status=$?
else
  status=124
fi
{
  printf 'driver_exit %s\n' "$status"
  if test -f "$out/trace.jsonl"; then sha256sum "$out/trace.jsonl"; fi
  date -u +%FT%TZ
} >> "$out/run.meta"
exit "$status"
