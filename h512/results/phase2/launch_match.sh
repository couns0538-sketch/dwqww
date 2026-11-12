#!/usr/bin/env bash
# launch_match.sh <id> <net file name in _work/nets> - JOB E phase 2: the exact command of each declared match.
#   mn1 / mn2 : fixed 250,000 nodes per move, no clock (h512/tools/run_match_nodes.sh)
#   m2        : 6 s + 0.06 s   (fair_eval/tools/run_match.sh, as in phase 1)
#   m3        : 10 s + 0.1 s, 2,000 games (addendum 7)   (fair_eval/tools/run_match.sh)
#   m5        : 6 s + 0.06 s, a later candidate
# Every match: 3,000 games unless noted, 12 at once, candidate exe of phase 1, against the original lock exe.
set -u
id="$1"; net="$2"
D=/d/forge_jobs_20261111/h512E
C="$D/_work/builds/h512_v3_d59e905d3372/forge_fair_h512_v3.exe"
N="D:/forge_jobs_20261111/h512E/_work/nets/$net"
[ -f "$D/_work/nets/$net" ] || { echo "no such net: $net"; exit 2; }
O="option.NNUEArchFile=$N option.NNUEArch=true"
R="$D/_work/match"
tag="${net%.fnn3}"; tag="${tag#h512_cand_seen}"
case "$id" in
  mn1) MATCH_NODES=250000 MATCH_SEED=2026111108 bash "$D/h512/tools/run_match_nodes.sh" "mn1_nodes250k_$tag" "$R" 3000 "$C" "$O" ;;
  mn2) MATCH_NODES=250000 MATCH_SEED=2026111109 bash "$D/h512/tools/run_match_nodes.sh" "mn2_nodes250k_$tag" "$R" 3000 "$C" "$O" ;;
  m2)  mkdir -p "$R/_cwd_m2" && cd "$R/_cwd_m2" && MATCH_TC=6+0.06 MATCH_SEED=2026111106 bash "$D/fair_eval/tools/run_match.sh" "m2_tc6_$tag" "$R" 3000 "$C" "$O" ;;
  m3)  mkdir -p "$R/_cwd_m3" && cd "$R/_cwd_m3" && MATCH_TC=10+0.1 MATCH_SEED=2026111107 bash "$D/fair_eval/tools/run_match.sh" "m3_tc10_$tag" "$R" 2000 "$C" "$O" ;;
  m5)  mkdir -p "$R/_cwd_m5" && cd "$R/_cwd_m5" && MATCH_TC=6+0.06 MATCH_SEED=2026111110 bash "$D/fair_eval/tools/run_match.sh" "m5_tc6_$tag" "$R" 3000 "$C" "$O" ;;
  *) echo "unknown match id $id"; exit 2 ;;
esac
