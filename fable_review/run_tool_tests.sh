#!/usr/bin/env bash
# Run every Sol tool job's own Python tests from an exported copy of its folder (read-only branches untouched).
# Trainer-related tests are skipped: they import the production trainer by a name the PC rules forbid to run.
set -u
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
ROOT=/f/opus_scratch/fable_review/tooltests
OUT=/f/opus_scratch/fable_review/tool_tests.txt
mkdir -p "$ROOT"
: > "$OUT"
cd /f/opus_scratch/fable_wt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=/f/opus_scratch/fable/tmp TEMP=/f/opus_scratch/fable/tmp
run_test() {
  local branch=$1 job=$2 test=$3
  local dir="$ROOT/$branch"
  if [ ! -d "$dir/opus_round1/$job" ]; then
    mkdir -p "$dir"
    git archive "origin/$branch" "opus_round1/$job" | tar -x -C "$dir"
  fi
  local tdir="$dir/$(dirname "$test")"
  local tfile="$(basename "$test")"
  local log="$ROOT/${branch}_${tfile%.py}.log"
  ( cd "$tdir" && timeout --kill-after=10 300 nice -n 19 "$PY" -B "$tfile" > "$log" 2>&1 )
  local rc=$?
  local summary
  summary=$(grep -E -i "passed|failed|ok$|OK|FAIL|Error" "$log" | tail -1 | cut -c1-120)
  echo "$branch | $test | exit $rc | $summary" >> "$OUT"
}
while read -r branch job test; do
  case "$test" in
    *v3c*|*v3d*|*trainer_clip*|*S09_v2*|*S18*) echo "$branch | $test | SKIPPED (imports the production trainer)" >> "$OUT"; continue;;
  esac
  run_test "$branch" "$job" "$test"
done <<'LIST'
opus-sol-A7 sol_A7 opus_round1/sol_A7/test_opus_a7.py
opus-sol-S05fix sol_S05fix opus_round1/sol_S05fix/test_forge_sol_S05_fmacheck_v4.py
opus-sol-S06fix sol_S06fix opus_round1/sol_S06fix/test_forge_sol_S06_cli_v2.py
opus-sol-S06fix sol_S06fix opus_round1/sol_S06fix/test_forge_sol_S06_logs_v2.py
opus-sol-S06fix sol_S06fix opus_round1/sol_S06fix/test_forge_sol_S06_pgn_v2.py
opus-sol-S06fix sol_S06fix opus_round1/sol_S06fix/test_forge_sol_S06_statistics_v2.py
opus-sol-S06fix sol_S06fix opus_round1/sol_S06fix/test_forge_sol_S06_v2_fixups.py
opus-sol-S08fix sol_S08fix opus_round1/sol_S08fix/test_forge_sol_S08_collect_v2.py
opus-sol-S09fix sol_S09fix opus_round1/sol_S09fix/test_forge_sol_S09_v2.py
opus-sol-S10fix sol_S10fix opus_round1/sol_S10fix/test_opus_s10fix.py
opus-sol-S12 sol_S12 opus_round1/sol_S12/test_jobA_cause.py
opus-sol-S14 sol_S14 opus_round1/sol_S14/test_picker_audit.py
opus-sol-S15 sol_S15 opus_round1/sol_S15/test_forge_sol_S15_spsa_v2.py
opus-sol-S16 sol_S16 opus_round1/sol_S16/test_forge_sol_S16_overlap_scan.py
opus-sol-S19 sol_S19 opus_round1/sol_S19/test_forge_sol_S19_wdl_scale_fit.py
opus-sol-S21 sol_S21 opus_round1/sol_S21/test_forge_sol_S21_int16range.py
opus-sol-S25fix sol_S25fix opus_round1/sol_S25fix/test_forge_sol_S25_outcontract_v2_20261027.py
opus-sol-S26fix sol_S26fix opus_round1/sol_S26fix/test_forge_sol_S26fix_20261027.py
opus-sol-S27fix sol_S27fix opus_round1/sol_S27fix/test_forge_sol_S27_v2_20261027.py
opus-sol-S28fix sol_S28fix opus_round1/sol_S28fix/test_forge_sol_S28_proposal_v3_20261027.py
opus-sol-S30 sol_S30 opus_round1/sol_S30/test_forge_sol_S30.py
opus-sol-S31 sol_S31 opus_round1/sol_S31/test_forge_sol_S31_avg_ckpt.py
opus-sol-S33fix sol_S33fix opus_round1/sol_S33fix/test_forge_sol_S33_labels_v2_20261027.py
opus-sol-S34 sol_S34 opus_round1/sol_S34/test_validate_manifest_v2.py
opus-sol-S36 sol_S36 opus_round1/sol_S36/test_forge_sol_S36.py
opus-sol-S38 sol_S38 opus_round1/sol_S38/test_gate_time_audit.py
opus-sol-S40 sol_S40 opus_round1/sol_S40/test_forge_sol_S40_merge_datagen_20261027.py
opus-sol-S42 sol_S42 opus_round1/sol_S42/test_forge_sol_S42_20261027.py
opus-sol-S43 sol_S43 opus_round1/sol_S43/test_forge_sol_S43_netbatch_v5_20261027.py
opus-sol-S44 sol_S44 opus_round1/sol_S44/test_forge_sol_S44.py
opus-sol-S45 sol_S45 opus_round1/sol_S45/test_forge_sol_S45_rebase_ready.py
opus-sol-S46 sol_S46 opus_round1/sol_S46/test_promote_sim.py
opus-sol-S47 sol_S47 opus_round1/sol_S47/test_autolock_audit.py
opus-sol-S48fix sol_S48fix opus_round1/sol_S48fix/test_forge_sol_S48_gate_guard_v2_20261027.py
opus-sol-S49 sol_S49 opus_round1/sol_S49/tests/test_pc_speed_ci.py
opus-sol-SA6 sol_SA6 opus_round1/sol_SA6/test_opus_sa6.py
opus-sol-SC4 sol_SC4 opus_round1/sol_SC4/test_opus_sc4.py
LIST
echo "DONE" >> "$OUT"
cat "$OUT"
