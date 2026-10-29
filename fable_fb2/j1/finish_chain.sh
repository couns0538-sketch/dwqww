#!/usr/bin/env bash
# FB2-J1 finishing chain: box build of forge_fable_v3.exe, OFF identity, NPS vs AL1 with the given net, 200 sanity
# games vs AL1 (100 per colour, 1+0.01, python-chess legality, flag detection), exact score on the full 1M-row subset.
# usage: finish_chain.sh <net.fnn3> <tag>      (one CPU thread; nice 19)
set -uo pipefail
NET=$1; TAG=$2
WT=/f/opus_scratch/worktrees/fable_fb2_j1
T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
L=/f/opus_scratch/fable/fb2/j1/finish_$TAG
EXE=/f/opus_scratch/build/fable_fb2/forge_fable_v3.exe
GAMES=/f/opus_scratch/worktrees/fable_fb2_j4/tools/timeman/fable_timeman_games.py
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$L"
cd "$WT"
if [ ! -f "$EXE" ]; then
  FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp" nice -n 19 bash $T/build_pc.sh "$PWD" "$EXE" > "$L/build_pc_v3.log" 2>&1
  echo "build exit $?" >> "$L/build_pc_v3.log"; echo "warnings $(grep -ci warning "$L/build_pc_v3.log")" >> "$L/build_pc_v3.log"
  nice -n 19 $PY -I -B $LA/2_build/uci_check.py "$EXE" --full > "$L/identity_off_v3.log" 2>&1; echo "identity exit $?" >> "$L/identity_off_v3.log"
fi
NETW=$(cygpath -w "$NET")
nice -n 19 $PY -I -B tools/nnue/fable_nnue_nps.py "$EXE" "$NETW" 3 16 20 > "$L/nps_vs_al1.log" 2>&1; echo "nps exit $?" >> "$L/nps_vs_al1.log"
nice -n 19 $PY -I -B "$GAMES" "$EXE" --tc 1+0.01 --games 100 --opt-white "NNUEArchFile=$NETW" --opt-white NNUEArch=true --seed 101 --out "$L/games_v3_white.json" > "$L/games_v3_white.log" 2>&1; echo "games white exit $?" >> "$L/games_v3_white.log"
nice -n 19 $PY -I -B "$GAMES" "$EXE" --tc 1+0.01 --games 100 --opt-black "NNUEArchFile=$NETW" --opt-black NNUEArch=true --seed 102 --out "$L/games_v3_black.json" > "$L/games_v3_black.log" 2>&1; echo "games black exit $?" >> "$L/games_v3_black.log"
nice -n 19 $PY -I -B tools/nnue/fable_nnue_train.py score --net "$NETW" --pos F:/opus_scratch/sol_S31/inputs/prod/holdout_013_014_s16.pos --hce F:/opus_scratch/sol_S31/inputs/prod/holdout_013_014_s16.hce --phases > "$L/score_full_subset.log" 2>&1; echo "score exit $?" >> "$L/score_full_subset.log"
echo "chain done" >> "$L/score_full_subset.log"
