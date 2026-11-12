#!/usr/bin/env bash
# launch_m8.sh - match M8 (h512/results/phase3/M8_DECLARATION.md): the rebuilt executable with candidate 3's net
# against the lock at 30 s + 0.3 s, 1,000 games, seed 2026111201 (fair_eval/tools/run_match.sh).
set -u
D=/d/forge_jobs_20261111/h512E
C="$D/_work/builds/h512_v3_c3_29ea1b67b2dd/forge_fair_h512_v3_c3.exe"
N="D:/forge_jobs_20261111/h512E/_work/nets/h512_cand_W2_seen10000023552.fnn3"
O="option.NNUEArchFile=$N option.NNUEArch=true"
R="$D/_work/match"
mkdir -p "$R/_cwd_m8" && cd "$R/_cwd_m8" && MATCH_TC=30+0.3 MATCH_SEED=2026111201 bash "$D/fair_eval/tools/run_match.sh" "m8_tc30_rebuilt_exe_cand3" "$R" 1000 "$C" "$O"
