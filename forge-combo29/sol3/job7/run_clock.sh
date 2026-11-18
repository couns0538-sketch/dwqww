#!/usr/bin/env bash
set -euo pipefail
root=/workspace/work/sol3-job7
job=forge-combo29/sol3/job7
old=/workspace/work/sol3-job4
runner=/workspace/work/sol3-job7-clock/movetime.py
positions=forge-combo29/sol3/job3/positions.txt
cutoff=$(date -u -d 2026-11-18T12:08:53Z +%s)
mkdir "$job/clock_harness"
cp "$runner" /workspace/work/sol3-job7-clock/mock.raw.txt "$job/clock_harness/"
cp "$root/run_clock.sh" "$job/"
for arm in 10 11; do
  out="$root/clock_k$arm"
  receipt="$root/clock_k$arm.command.txt"
  remaining=$((cutoff-$(date -u +%s)))
  if ((remaining<=0)); then break; fi
  export PYTHONPATH=/workspace/work/sol3-replay/python:/workspace/work/forge-sol3/forge-combo29/sol3/job4
  {
    printf 'PYTHONPATH=%q python3 -B %q k%s %q %q %q\n' "$PYTHONPATH" "$runner" "$arm" "$old/build_$arm/forge" "$positions" "$out"
    date -u +%FT%TZ
  } > "$receipt"
  status=0
  timeout --kill-after=5s "$remaining" python3 -B "$runner" "k$arm" "$old/build_$arm/forge" "$positions" "$out" > "$root/clock_k$arm.driver.stdout.json" 2> "$root/clock_k$arm.driver.stderr.txt" || status=$?
  printf 'exit_code %s\n' "$status" >> "$receipt"
  mkdir "$job/clock_k$arm"
  cp "$receipt" "$root/clock_k$arm.driver.stdout.json" "$root/clock_k$arm.driver.stderr.txt" "$job/clock_k$arm/"
  if [ -d "$out" ]; then cp "$out/"* "$job/clock_k$arm/"; fi
  date -u "+%Y-%m-%dT%H:%M:%SZ Step 2 ordinary k$arm clock run exited $status" >> "$job/stamps.txt"
  git add --sparse -- "$job/"
  git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check
  git -c user.name=sol3 -c user.email=sol3@users.noreply.github.com commit -qm "sol3 job 7 step 2 record clock and legality k$arm"
  bash /workspace/work/sol3-job3/push-checkpoint.sh
  if test -s "$out/summary.json"; then
    python3 - "$out/summary.json" <<'PY'
import json,sys
from pathlib import Path
row=json.loads(Path(sys.argv[1]).read_text())
print({key:row[key] for key in ('tree','timed_bestmoves','every_reported_bestmove_legal','median_wall_ms','max_wall_ms','error')})
PY
  fi
done
