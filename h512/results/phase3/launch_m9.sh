#!/usr/bin/env bash
# launch_m9.sh - match M9 (h512/results/phase3/M9_DECLARATION.md): the 1024-unit pilot net against candidate 3's net
# on the same executable, 10 s + 0.1 s, 2,000 games, seed 2026111202 (fair_eval/tools/run_match.sh).
set -u
D=/d/forge_jobs_20261111/h512E
E="$D/_work/builds/h512_v3_c3_b3c746944937/forge_fair_h512_v3_c3.exe"
NW="D:/forge_jobs_20261111/h512E/_work/runs/arms/h1024_pilot/net_seen10000023552.fnn3"
NC="D:/forge_jobs_20261111/h512E/_work/nets/h512_cand_W2_seen10000023552.fnn3"
R="$D/_work/match"
mkdir -p "$R/_cwd_m9" && cd "$R/_cwd_m9" && MATCH_TC=10+0.1 MATCH_SEED=2026111202 MATCH_BASE="$E" MATCH_BASE_NAME=c3 \
  MATCH_BASE_OPTS="option.NNUEArchFile=$NC option.NNUEArch=true" \
  bash "$D/fair_eval/tools/run_match.sh" "m9_tc10_h1024_pilot_vs_cand3" "$R" 2000 "$E" "option.NNUEArchFile=$NW option.NNUEArch=true"
