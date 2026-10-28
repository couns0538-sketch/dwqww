#!/usr/bin/env bash
# Re-run an Opus engine job's planted-bug (mutation) check from a fresh LF export of its branch head.
# usage: fable_nnue_mutants.sh <job>...     (job names from the TABLE below)
# Each job: F:/opus_scratch/fable_review/mutants/<job>/{root,scratch,run.log}. Idle priority, JOBS=2.
set -u
export PATH="/c/msys64/ucrt64/bin:/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin:/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja:$PATH"
REPO=/f/opus_scratch/worktrees/fable_review
BASE=/f/opus_scratch/fable_review/mutants
export JOBS=2 CXX=g++ MUTATION_LINK_FLAGS=-static MUTATION_FLAGS=-static PYTHON=python3

# job|branch|script|kind   (kind: sh = "<script> <scratch>" from the root; sh_j3 = same, with -j 3 lowered to JOBS)
TABLE="
O3|opus-O3|opus_round1/O3/mutation_check.sh|sh_j3
C2|opus-C2|opus_round1/C2/mutation_check.sh|sh
C4|opus-C4|opus_round1/C4/mutation_check.sh|sh
C4fl|opus-C4|opus_round1/C4/mutation_check_failloud.sh|sh
C5|opus-C5|opus_round1/C5/mutation_check.sh|sh
O4|opus-O4|opus_round1/O4/mutation_check.sh|sh
O5|opus-O5|opus_round1/O5/mutation_check.sh|sh
O6|opus-O6|opus_round1/O6/mutation_check.sh|sh
O7|opus-O7|opus_round1/O7/mutation_check.sh|sh
O8|opus-O8|opus_round1/O8/mutation_check.sh|sh
"

export_branch() { # branch dest
  mkdir -p "$2"
  git -C "$REPO" -c core.autocrlf=false archive "origin/$1" | tar -x -C "$2"
}

for job in "$@"; do
  line=$(printf '%s\n' "$TABLE" | grep "^$job|") || { echo "unknown job $job"; continue; }
  IFS='|' read -r _ branch script kind <<< "$line"
  D="$BASE/$job"
  if [ -e "$D/run.log" ]; then echo "$job: run.log exists, skipping (no deletes)"; continue; fi
  mkdir -p "$D"
  echo "[$(date +%H:%M:%S)] $job: export origin/$branch ($(git -C "$REPO" rev-parse --short "origin/$branch"))" | tee -a "$BASE/runner.log"
  export_branch "$branch" "$D/root"
  if [ "$kind" = sh_j3 ]; then sed -i 's/-j 3\b/-j "${JOBS:-1}"/' "$D/root/$script"; fi
  ( cd "$D/root" && { echo "# $job: origin/$branch $(git -C "$REPO" rev-parse "origin/$branch") script $script kind $kind JOBS=$JOBS $(date)";
      nice -n 19 bash "$script" "$D/scratch"; echo "exit $?"; date; } > "$D/run.log" 2>&1 )
  echo "[$(date +%H:%M:%S)] $job: $(grep -c -- '-> caught' "$D/run.log") caught, $(grep -c -- 'NOT caught' "$D/run.log") not caught, $(grep -c 'build failed\|pattern not found' "$D/run.log") broken, $(tail -2 "$D/run.log" | head -1)" | tee -a "$BASE/runner.log"
done
