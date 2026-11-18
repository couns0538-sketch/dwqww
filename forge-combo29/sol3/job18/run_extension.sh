#!/usr/bin/env bash
set -euo pipefail
job=forge-combo29/sol3/job18
prior=forge-combo29/sol3/job17
for arm in A B D C E G F; do
  rg -Fxq 'exit_code 0' "$job/census/$arm/run.meta"
  test "$(wc -l < "$job/census/$arm/rows.tsv")" -eq 121
done
claim=$(awk 'NR==1 {print $1}' "$job/stamps.txt")
cutoff=$(($(date -u -d "$claim" +%s) + 3000))
if (($(date -u +%s) >= cutoff)); then
  printf 'Minute 50 crossed before Part 2.\n'
  exit 0
fi
mkdir -p "$job/part2"
python3 - "$prior/positions.txt" "$job/part2/row24.txt" <<'PY'
from pathlib import Path
import sys

source, target = map(Path, sys.argv[1:])
fen, game, plies = source.read_text(encoding='ascii').splitlines()[23].split('\t')
assert (fen, game, plies) == ('8/8/kp3QK1/p2R4/2p5/3n4/PP6/8 w - - 6 49', '8', '7')
pieces = sum(char in 'PNBRQKpnbrqk' for char in fen.split()[0])
target.write_text(f'{fen}\t{game}\t{plies}\t{pieces}\n', encoding='ascii')
PY
for arm in D A; do
  if (($(date -u +%s) >= cutoff)); then
    printf 'Minute 50 crossed before Part 2 %s.\n' "$arm"
    break
  fi
  run_code=0
  out="$job/part2/$arm"
  bash "$job/run_one.sh" extension "$arm" "$out" "$job/part2/row24.txt" || run_code=$?
  printf '%s Part 2 Job 17 row 24 %s depth22 run exit %s\n' "$(date -u +%FT%TZ)" "$arm" "$run_code" >> "$job/stamps.txt"
  git add -- "$job"
  git commit -m "sol3 job 18 Part 2 retain row 24 $arm depth22"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if ((run_code != 0)); then
    cat "$out/driver.stderr.txt"
    exit "$run_code"
  fi
  tail -1 "$out/rows.tsv"
done
