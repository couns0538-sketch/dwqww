#!/usr/bin/env bash
# R3-6Q: runner record (nproc, lscpu) and speed check: Threads=1 `off` at full depth on every 5th position
# (6 of 30), compared with the PC's R3-6 times -> depth_offset (written to $GITHUB_OUTPUT when set).
# usage: ci_speed.sh <forge> <log_dir>
set -euo pipefail
FORGE=$1; LOG=$2
H=$(cd "$(dirname "$0")" && pwd)
POS="$H/../R3-6/positions30.tsv"
mkdir -p "$LOG"
{ echo "nproc: $(nproc)"; lscpu; echo; uptime; } > "$LOG/runner_prep.txt"
grep -E '^(nproc|Model name|Thread\(s\) per core|Core\(s\) per socket|CPU\(s\)|L3)' "$LOG/runner_prep.txt" || true
IDS=$(grep -v '^#' "$POS" | awk -F'\t' 'NR % 5 == 1 {print $1}' | paste -sd, -)
echo "speed sample: $IDS"
python3 "$H/smp_ttd_linux.py" --positions "$POS" --config "off=$FORGE" --threads 1 --rep 0 --only "$IDS" \
  --hash 64 --out "$LOG/speed_t1.jsonl" | tee "$LOG/speed_t1.log"
python3 "$H/choose_depth.py" "$LOG/speed_t1.jsonl" "$H/../R3-6/logs/ttd_per_position.tsv" | tee "$LOG/speed_check.md"
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  grep '^depth_offset=' "$LOG/speed_check.md" | tail -1 >> "$GITHUB_OUTPUT"
fi
