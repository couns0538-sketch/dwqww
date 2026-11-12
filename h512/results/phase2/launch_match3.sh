#!/usr/bin/env bash
# launch_match3.sh m6 <net file name in _work/nets> - JOB E phase 2 (addendum 10): candidate 4 against the lock.
#   m6 : 6 s + 0.06 s, 2,000 games, seed 2026111111   (fair_eval/tools/run_match.sh, as in M2 and M5)
# A separate file because a launcher must not be edited while a match started through it runs.
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
  m6)  mkdir -p "$R/_cwd_m6" && cd "$R/_cwd_m6" && MATCH_TC=6+0.06 MATCH_SEED=2026111111 bash "$D/fair_eval/tools/run_match.sh" "m6_tc6_$tag" "$R" 2000 "$C" "$O" ;;
  *) echo "unknown match id $id"; exit 2 ;;
esac
