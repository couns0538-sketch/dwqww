#!/usr/bin/env bash
# launch_match2.sh <id> <net file name in _work/nets> - JOB E phase 2: the exact command of the later matches
# (addendum 8). A separate file because launch_match.sh must not be edited while a match started through it runs.
#   m5  : 6 s + 0.06 s, 2,000 games, seed 2026111110   (fair_eval/tools/run_match.sh, as in phase 1 and M2)
#   mn2 : fixed 250,000 nodes per move, no clock, 3,000 games, seed 2026111109   (h512/tools/run_match_nodes.sh)
# 12 games at once, candidate exe of phase 1, against the original lock exe.
set -u
id="$1"; net="$2"
D=/d/forge_jobs_20261111/h512E
C="$D/_work/builds/h512_v3_d59e905d3372/forge_fair_h512_v3.exe"
N="D:/forge_jobs_20261111/h512E/_work/nets/$net"
[ -f "$D/_work/nets/$net" ] || { echo "no such net: $net"; exit 2; }
O="option.NNUEArchFile=$N option.NNUEArch=true"
R="$D/_work/match"
tag="${net%.fnn3}"
case "$id" in
  m5)  mkdir -p "$R/_cwd_m5" && cd "$R/_cwd_m5" && MATCH_TC=6+0.06 MATCH_SEED=2026111110 bash "$D/fair_eval/tools/run_match.sh" "m5_tc6_$tag" "$R" 2000 "$C" "$O" ;;
  mn2) MATCH_NODES=250000 MATCH_SEED=2026111109 bash "$D/h512/tools/run_match_nodes.sh" "mn2_nodes250k_$tag" "$R" 3000 "$C" "$O" ;;
  *) echo "unknown match id $id"; exit 2 ;;
esac
