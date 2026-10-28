#!/usr/bin/env bash
# Run the four job tests that need a full checkout (repository files, a git work tree, exe fixtures) inside real
# worktrees of their opus branches (read-only use; nothing committed there).
set -u
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
OUT=/f/opus_scratch/fable_review/fullcheckout_tests.txt
: > "$OUT"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=/f/opus_scratch/fable/tmp TEMP=/f/opus_scratch/fable/tmp
cd /f/opus_scratch/fable_wt
while read -r branch job test; do
  W=/f/opus_scratch/worktrees/review_full_$job
  if [ ! -d "$W" ]; then
    git worktree add -q --detach "$W" "origin/$branch" 2>>"$OUT" || { echo "$branch | worktree failed" >> "$OUT"; continue; }
  fi
  log=/f/opus_scratch/fable_review/tooltests/full_${branch}_$(basename "$test" .py).log
  ( cd "$W/$(dirname "$test")" && timeout --kill-after=10 900 nice -n 19 "$PY" -B "$(basename "$test")" > "$log" 2>&1 )
  rc=$?
  summary=$(grep -E -i "passed|failed|^OK|FAIL|Error" "$log" | tail -1 | cut -c1-120)
  echo "$branch | $test | exit $rc | $summary" >> "$OUT"
done <<'LIST'
opus-sol-S15 sol_S15 opus_round1/sol_S15/test_forge_sol_S15_spsa_v2.py
opus-sol-S27fix sol_S27fix opus_round1/sol_S27fix/test_forge_sol_S27_v2_20261027.py
opus-sol-S47 sol_S47 opus_round1/sol_S47/test_autolock_audit.py
opus-sol-S48fix sol_S48fix opus_round1/sol_S48fix/test_forge_sol_S48_gate_guard_v2_20261027.py
LIST
echo DONE >> "$OUT"
cat "$OUT"
