#!/usr/bin/env bash
# Re-run the Python-style / special planted-bug checks of the Opus engine jobs from fresh LF exports.
# usage: fable_nnue_mutants_py.sh <job>...   jobs: A1 SA2 SA4 S12 S12alias S41 C6 R3-4 R3-5 R3-6 portc portc_o2 O2 S14 S14zf S08fix SIT C1
set -u
export PATH="/c/msys64/ucrt64/bin:/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin:/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja:$PATH"
REPO=/f/opus_scratch/worktrees/fable_review
BASE=/f/opus_scratch/fable_review/mutants
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
TOOLS=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LOCKEXE=D:/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_h256_s198.exe
export JOBS=2 CXX=g++ MUTATION_LINK_FLAGS=-static MUTATION_FLAGS=-static PYTHON=python3
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1

branch_of() {
  case $1 in
    A1) echo opus-sol-A1;; SA2) echo opus-sol-SA2;; SA4) echo opus-sol-SA4;; S12|S12alias) echo opus-sol-S12;;
    S41) echo opus-sol-S41;; C6) echo opus-C6;; R3-4|R3-5|R3-6|portc|portc_o2) echo opus-r3-stack;; O2) echo opus-O2;;
    S14|S14zf) echo opus-sol-S14;; S08fix) echo opus-sol-S08fix;; SIT) echo opus-sol-SIT;; C1) echo opus-C1;;
    *) echo "";;
  esac
}

run_job() { # job  (cwd = exported root, $D = job dir, $S = scratch)
  local job=$1
  case $job in
    A1)      nice -n 19 "$PY" -I -B opus_round1/sol_A1/tools/mutation_check.py "$PWD" "$S";;
    SA2)     nice -n 19 "$PY" -I -B opus_round1/sol_SA2/mutation_check_sa2.py "$PWD" "$S";;
    SA4)     nice -n 19 "$PY" -I -B opus_round1/sol_SA4/mutation_check_sa4.py "$PWD" "$S";;
    S12)     nice -n 19 "$PY" -I -B opus_round1/sol_S12/mutation_check.py "$S";;
    S12alias) nice -n 19 "$PY" -I -B opus_round1/sol_S12/followup_nullalias/mutation_check_alias.py "$PWD" "$S";;
    S41)     nice -n 19 "$PY" -I -B opus_round1/sol_S41/mutation_check_engine_s41.py --tree "$PWD" --work "$S";;
    C6)      nice -n 19 python3 opus_round1/C6/mutation_check.py . "$S" -DCMAKE_EXE_LINKER_FLAGS=-static;;
    R3-4)    nice -n 19 "$PY" -I -B opus_r3/R3-4/r3_4_mutation_check.py "$PWD" "$S";;
    R3-5)    nice -n 19 "$PY" -I -B opus_r3/R3-5/tools/mutation_check.py "$PWD" "$S" --python "$PY";;
    R3-6)    nice -n 19 "$PY" -I -B opus_r3/R3-6/mutation_check.py . "$S";;
    portc)   nice -n 19 "$PY" -I -B opus_r3/port_c/mutation_check_port_c.py "$PWD" "$S";;
    portc_o2) nice -n 19 "$PY" -I -B opus_r3/port_c/mutation_check_port_c.py "$PWD" "$S" --o2;;
    O2)      nice -n 19 "$PY" -I -B opus_round1/O2/mutation_check.py "$PWD" "$S" "$TOOLS/cmake_build_flags.sh" "-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256";;
    S14)     ( cd opus_round1/sol_S14 && nice -n 19 "$PY" -I -B mutation_check.py "$S" --dis /f/opus_scratch/sol_s14/lock_exe.dis --exe "$LOCKEXE" );;
    S14zf)   nice -n 19 "$PY" -I -B opus_round1/sol_S14/followup_zerofill/mutation_check.py "$PWD" "$S" --ref-digest 46501e4f2dc86508;;
    S08fix)  # make_prof_mutant.py on a copy, FORGE_PROF=ON build of forge_prof_tests, the test must FAIL; green control must PASS
             for m in control merge_main_only shared_bank; do
               mkdir -p "$S/$m/tree" && cp -r CMakeLists.txt src include tests tools bench "$S/$m/tree/"
               if [ "$m" != control ]; then nice -n 19 "$PY" -I -B opus_round1/sol_S08fix/make_prof_mutant.py "$S/$m/tree" "$m" || { echo "MUTATION $m: generation failed"; continue; }; fi
               nice -n 19 cmake -S "$S/$m/tree" -B "$S/$m/build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_PROF=ON \
                 "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" -DCMAKE_EXE_LINKER_FLAGS=-static > "$S/$m/configure.log" 2>&1 || { echo "MUTATION $m: configure failed"; tail -3 "$S/$m/configure.log"; continue; }
               nice -n 19 cmake --build "$S/$m/build" --target forge_prof_tests -j "$JOBS" > "$S/$m/build.log" 2>&1 || { echo "MUTATION $m: build failed"; tail -3 "$S/$m/build.log"; continue; }
               nice -n 19 "$S/$m/build/forge_prof_tests" > "$S/$m/test.log" 2>&1; rc=$?
               if [ "$m" = control ]; then [ $rc -eq 0 ] && echo "CONTROL $m -> PASS (rc 0)" || echo "CONTROL $m -> FAILS (rc $rc)";
               else [ $rc -ne 0 ] && echo "MUTATION $m -> caught (rc $rc: $(grep -m1 -E 'FAIL' "$S/$m/test.log" | cut -c1-120))" || echo "MUTATION $m -> NOT caught (rc 0)"; fi
             done;;
    SIT)     nice -n 19 bash opus_round1/sol_SIT/build_unit_tests.sh "$PWD" "$S/baseobj" "$S/base_t.exe" > "$S.base_build.log" 2>&1 || { echo "base build failed"; tail -3 "$S.base_build.log"; return; }
             nice -n 19 "$S/base_t.exe" > "$S.base_run.log" 2>&1; echo "unmutated: rc $? $(tail -1 "$S.base_run.log")"
             nice -n 19 bash opus_round1/sol_SIT/run_mutants.sh "$PWD" "$S" "$S/baseobj" tt_cut tt_cut_search forced_draw null_window store twofold search_floor search_store probcut_store correction standpat_store qsearch_forced_draw placeholder_score_qsearch placeholder_score_search placeholder_via_score_to_tt fail_low_bonus dup_first_only castling_base mask_unset king_skipped;;
    C1)      tb=${C1_TB:-}; [ -n "$tb" ] && [ -d "$tb" ] || { echo "C1: no tablebase folder (set C1_TB)"; return; }
             nice -n 19 bash opus_round1/C1/mutation_check.sh "$PWD" "$S" "$tb";;
    *)       echo "unknown job $job";;
  esac
}

for job in "$@"; do
  branch=$(branch_of "$job"); [ -n "$branch" ] || { echo "unknown job $job"; continue; }
  D="$BASE/$job"; S="$D/scratch"
  if [ -e "$D/run.log" ]; then echo "$job: run.log exists, skipping (no deletes)"; continue; fi
  mkdir -p "$D/root"
  echo "[$(date +%H:%M:%S)] $job: export origin/$branch ($(git -C "$REPO" rev-parse --short "origin/$branch"))" | tee -a "$BASE/runner.log"
  git -C "$REPO" -c core.autocrlf=false archive "origin/$branch" | tar -x -C "$D/root"
  ( cd "$D/root" && { echo "# $job: origin/$branch $(git -C "$REPO" rev-parse "origin/$branch") JOBS=$JOBS $(date)"; run_job "$job"; echo "exit $?"; date; } > "$D/run.log" 2>&1 )
  echo "[$(date +%H:%M:%S)] $job: $(grep -c -i -E 'caught\b' "$D/run.log") caught lines, $(grep -c -i -E 'NOT caught|survived|SURVIVOR' "$D/run.log") not-caught lines, $(grep -c -i -E 'build failed|pattern not found|configure failed|Traceback' "$D/run.log") broken, $(tail -2 "$D/run.log" | head -1)" | tee -a "$BASE/runner.log"
done
