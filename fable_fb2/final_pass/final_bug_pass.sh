#!/usr/bin/env bash
# FB2 final 30-minute bug-test pass (user request 2026-10-28): re-run every job's tests and identity checks on the
# current branch heads, run short self-play / datagen / time-management smokes, and collect everything in one log.
# usage: final_bug_pass.sh     (one thread except the J5 unit test, which uses 3 threads for seconds)
set -uo pipefail
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
B=/f/opus_scratch/build/fable_fb2
L=/f/opus_scratch/fable/fb2/final_pass
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=/f/opus_scratch/fable/tmp TEMP=/f/opus_scratch/fable/tmp
mkdir -p "$L"
LOG="$L/final_pass.log"
: > "$LOG"
say() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
step() { # name command...
  local name=$1; shift
  say "== $name"
  ( "$@" ) > "$L/$name.log" 2>&1
  local rc=$?
  say "   $name exit $rc"
  return $rc
}
# 1. OFF identity of every box exe (lock pins)
for exe in forge_fable_j2 forge_fable_j3 forge_fable_j4 forge_fable_j5 forge_fable_v3; do
  step "identity_$exe" nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$B/$exe.exe" --full
  grep -q 'ALL OK' "$L/identity_$exe.log" && say "   ALL OK" || say "   NOT ALL OK"
done
# 2. unit tests of every job (CMake trees)
step unit_j2_datagen nice -n 19 "$B/j2_cmake/forge_datagen2_tests.exe" "$L/j2_scratch"
step unit_j3_options nice -n 19 "$B/j3_cmake/forge_fb2_j3_tests.exe"
step unit_j4_timeman nice -n 19 "$B/j4_cmake/forge_timeman_sim.exe" 2000 --seed 7
step unit_j4_timeman_stall nice -n 19 "$B/j4_cmake/forge_timeman_sim.exe" 1000 --seed 8 --stall-ms 8 --stall-prob 0.1
# (the J5 unit test needs 3 threads next to the training's one; it ran clean at 19:00 and is not repeated here)
step unit_j1_data nice -n 19 $PY -I -B /f/opus_scratch/worktrees/fable_fb2_j1/tools/nnue/test_fable_nnue_data.py "$L/j1_data_scratch"
step unit_j2_decoder nice -n 19 $PY -I -B /f/opus_scratch/worktrees/fable_fb2_j2/tools/nnue/fable_datagen_decode.py test "$B/forge_fable_j2.exe" "$L/j2_decoder"
# 3. smokes: datagen 2 min with the v3 net, J3 all-on 60 games, J4 v2 30 games, J5 SmpV2 Threads 3 30 games, v3 net 30 games
NET=$(cygpath -w /f/opus_scratch/fable/fb2/train_j1/best.fnn3)
step smoke_datagen_v3 bash -c "printf 'setoption name NNUEArchFile value $NET\nsetoption name NNUEArch value true\ndatagen --out $L/dg_v3 --max-minutes 2 --nodes 3000 --random-plies 8 --random-plies-jitter 4 --temp-plies 2 --opening-eval-cap 300 --min-ply 16 --skip-prob 0.25 --draw-cp 8 --draw-plies 10 --draw-min-ply 80 --seed 77 --pos\ndatagen convert $L/dg_v3.fgb $L/dg_v3_conv\nquit\n' | nice -n 19 $B/forge_fable_j2.exe"
step smoke_datagen_compare nice -n 19 $PY -I -B /f/opus_scratch/worktrees/fable_fb2_j2/tools/nnue/fable_datagen_decode.py compare "$L/dg_v3.fgb" "$L/dg_v3.pos"
cmp "$L/dg_v3.pos" "$L/dg_v3_conv.pos" && say "   datagen direct == converter .pos" || say "   DIFF datagen .pos"
cmp "$L/dg_v3.hce" "$L/dg_v3_conv.hce" && say "   datagen direct == converter .hce" || say "   DIFF datagen .hce"
GAMES=/f/opus_scratch/worktrees/fable_fb2_j4/tools/timeman/fable_timeman_games.py
step smoke_j3_allon_games nice -n 19 $PY -I -B $GAMES "$B/forge_fable_j3.exe" --tc 1+0.01 --games 60 --opt-white CorrHistV2=true --opt-white SingularV2=true --opt-white LmrTableV2=true --opt-white TtPruneV2=true --seed 201 --out "$L/j3_allon_games.json"
step smoke_j4_v2_games nice -n 19 $PY -I -B $GAMES "$B/forge_fable_j4.exe" --tc 0.5+0.005 --games 40 --opt-white TimeManV2=true --opt-black TimeManV2=true --seed 202 --out "$L/j4_v2_games.json"
step smoke_j5_smp_games nice -n 19 $PY -I -B $GAMES "$B/forge_fable_j5.exe" --tc 1+0.01 --games 30 --opt-white SmpV2=true --opt-white Threads=2 --opt-black SmpV2=true --opt-black Threads=2 --seed 203 --out "$L/j5_smp_games.json"
step smoke_v3_net_games nice -n 19 $PY -I -B $GAMES "$B/forge_fable_v3.exe" --tc 1+0.01 --games 40 --opt-white "NNUEArchFile=$NET" --opt-white NNUEArch=true --opt-black "NNUEArchFile=$NET" --opt-black NNUEArch=true --seed 204 --out "$L/v3_net_games.json"
# 4. parity of the latest net with the v3 tool (engine int == trainer int on 10k positions)
step parity_best_net bash -c "nice -n 19 $B/j5_cmake/forge_nnue_v3_tool.exe eval '$NET' F:/opus_scratch/fable/parity/positions_10k.fen > $L/best_engine_eval.txt && cd /f/opus_scratch/worktrees/fable_fb2_j1 && nice -n 19 $PY -I -B tools/nnue/fable_nnue_v3.py compare '$NET' F:/opus_scratch/fable/parity/positions_10k.fen $L/best_engine_eval.txt"
say "final pass done"
