#!/bin/bash
# Job 25 match driver with node/start readback checks. Usage:
# job25_match.sh <M> <seed> <start> <nodes> <rounds> <fhb_value>
set -u
M=$1; SEED=$2; START=$3; NODES=$4; ROUNDS=$5; FHB=$6
EXE=/tmp/forgebuild_bfhb/forge
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
CMD="/tmp/fastchess/fastchess -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $S14 option.FailHighBlend=$FHB -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $S14 option.FailHighBlend=0 -each proto=uci nodes=$NODES -openings file=/tmp/evid/openings_job25.epd format=epd order=sequential start=$START -srand $SEED -rounds $ROUNDS -games 2 -repeat -concurrency 4 -recover -ratinginterval 100 -pgnout file=$M.pgn min=true"
GOT=$(printf '%s' "$CMD" | grep -o 'nodes=[0-9]*' | sort -u | tr '\n' ' ')
GOTSTART=$(printf '%s' "$CMD" | grep -o 'start=[0-9]*' | sort -u | tr '\n' ' ')
if [ "$GOT" != "nodes=$NODES " ] || [ "$GOTSTART" != "start=$START " ]; then
  echo "READBACK FAILED: expected nodes=$NODES start=$START; got: $GOT $GOTSTART - ABORTED" >&2
  exit 1
fi
J=/agent/repos/dwqww/forge-combo29/tests_glmflash5_job25
printf '%s\n' "$CMD" > "$J/cmd_$M.txt"
echo "$(date -u +%FT%TZ) cmd_$M.txt written (readback OK: $GOT $GOTSTART; cand FHB=$FHB, base FHB=0); launching $M" >> "$J/stamps.txt"
t0=$(date -u +%s)
eval "$CMD" > /tmp/evid/${M}_stdout.txt 2>&1
rc=$?
echo "$(date -u +%FT%TZ) $M finished rc=$rc after $(( $(date -u +%s) - t0 ))s" >> "$J/stamps.txt"
tail -8 /tmp/evid/${M}_stdout.txt
