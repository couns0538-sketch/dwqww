#!/usr/bin/env bash
# launch_match4.sh m7 - JOB E phase 2 (addendum 11): the rebuilt executable with candidate 3's net against the lock.
#   m7 : 6 s + 0.06 s, 1,500 games, seed 2026111112   (fair_eval/tools/run_match.sh, as in phase 1, M2 and M5)
set -u
id="$1"
D=/d/forge_jobs_20261111/h512E
C="$D/_work/builds/h512_v3_c3_29ea1b67b2dd/forge_fair_h512_v3_c3.exe"
N="D:/forge_jobs_20261111/h512E/_work/nets/h512_cand_W2_seen10000023552.fnn3"
O="option.NNUEArchFile=$N option.NNUEArch=true"
R="$D/_work/match"
case "$id" in
  m7)  mkdir -p "$R/_cwd_m7" && cd "$R/_cwd_m7" && MATCH_TC=6+0.06 MATCH_SEED=2026111112 bash "$D/fair_eval/tools/run_match.sh" "m7_tc6_rebuilt_exe_cand3" "$R" 1500 "$C" "$O" ;;
  *) echo "unknown match id $id"; exit 2 ;;
esac
