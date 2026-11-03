#!/usr/bin/env bash
# prep_baseline.sh - Opus R14-B: prepare speed of the frozen proof code (5c88438f, the baseline) vs the current code
# (--jobs 1 and --jobs 2) on the same 200,000 rows, order F J1 J2 J2 J1 F; rows.tsv must be identical in all six.
set -u
out=/c/o14b/r2/meas3
I2=/d/grok-pc-data/dwqww/.claude/worktrees/o14b-r2/opus_r14b/item2
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
in=/c/o14b/r2/meas/in220k.txt
[ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }
mkdir -p "$out/frozen_code/astra"
cp /c/o14b/r2/frozen_relabel2.py "$out/frozen_code/relabel2.py"
cp "$I2/astra/records.py" "$out/frozen_code/astra/records.py"
cp "$I2/forge_probe.py" "$out/frozen_code/forge_probe.py"
echo "frozen $(sha256sum < "$out/frozen_code/relabel2.py" | cut -c1-16), current $(sha256sum < "$I2/relabel2.py" | cut -c1-16)"
num() { sed -n "s/.*\"$2\": \([0-9]*\).*/\1/p" "$1" | head -1; }
k=0
for spec in "F 1" "C 1" "C 2" "C 2" "C 1" "F 1"; do
  set -- $spec
  k=$((k + 1))
  j=$out/p${k}_$1$2
  code=$I2/relabel2.py; extra="--jobs $2"
  [ "$1" = F ] && { code=$out/frozen_code/relabel2.py; extra=""; }
  t0=$(date +%s.%N)
  "$PY" -I -B "$code" prepare --job "$j" --run-id "p$k" --rows 200000 --selfplay "$in" $extra > /dev/null || exit $?
  t1=$(date +%s.%N)
  awk -v n="p${k}_$1$2" -v r="$(num "$j/prepare.json" rows)" -v a="$t0" -v b="$t1" -v h="$(sha256sum < "$j/rows.tsv" | cut -c1-16)" \
    'BEGIN {printf "%s rows=%d wall_s=%.1f rows_per_hour=%.0f rows_tsv=%s\n", n, r, b - a, r * 3600 / (b - a), h}'
done
