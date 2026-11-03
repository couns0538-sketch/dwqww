#!/usr/bin/env bash
# w2_pgo.sh - Opus R14-B: 2 probe workers (mask 0xC = one physical core), R13 probe vs LTO+PGO probe, order R P P R,
# the same 19,927 rows each time; labels.tsv must be identical in all four. Then the sha256 speed of relabel2's
# file_hash on a 645 MB self-play file (the fixed input-hashing cost of prepare).
set -u
out=/c/o14b/r2/meas_w2pgo
I2=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-r2/opus_r14b/item2
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
in=/c/o14b/r2/meas/in220k.txt
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out"
num() { sed -n "s/.*\"$2\": \([0-9]*\).*/\1/p" "$1" | head -1; }
k=0
for arm in R P P R; do
  k=$((k + 1))
  probe='C:\o13\p5\forge_data_probe.exe'; [ "$arm" = P ] && probe='C:\o14b\pgo2\pgo\forge_data_probe.exe'
  j=$out/w2_${k}_$arm
  "$PY" -I -B "$I2/relabel2.py" prepare --job "$j" --run-id "w2$k" --rows 20000 --selfplay "$in" > /dev/null || exit $?
  t0=$(date +%s.%N)
  "$PY" -I -B "$I2/relabel2.py" run --job "$j" --run-id "w2$k" --probe "$probe" --nodes 20000 --workers 2 --mask 0xC \
    --shard-size 10000 > /dev/null || exit $?
  t1=$(date +%s.%N)
  "$PY" -I -B "$I2/relabel2.py" assemble --job "$j" --run-id "w2$k" > /dev/null || exit $?
  awk -v n="w2_${k}_$arm" -v r="$(num "$j/prepare.json" rows)" -v a="$t0" -v b="$t1" \
    -v md5="$(md5sum < "$j/final/labels.tsv" | cut -c1-32)" -v now="$(date '+%T')" \
    'BEGIN {printf "%s rows=%d run_wall_s=%.1f rows_per_hour=%.0f labels_md5=%s %s\n", n, r, b - a, r * 3600 / (b - a), md5, now}'
done
"$PY" -I -B -c "
import sys, time
sys.path.insert(0, sys.argv[1])
import relabel2
t = time.perf_counter()
h = relabel2.file_hash(sys.argv[2])
dt = time.perf_counter() - t
import os
mb = os.path.getsize(sys.argv[2]) / 1e6
print(f'file_hash on {mb:.0f} MB: {dt:.2f} s = {mb / dt:.0f} MB/s')
" "$I2" /d/grok-pc-data/selfplay_out/forge_selfplay_003.txt
