#!/bin/bash
# Queue 3 match driver with node/start readback checks.
# Usage: queue3_match.sh <M> <seed> <start> <nodes> <setting>  (VT|VP|N0)
set -u
M=$1; SEED=$2; START=$3; NODES=$4; S=$5
EXE_BVT=/tmp/forgebuild_bvt/forge
EXE_BVP=/tmp/forgebuild_bvp/forge
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
extra=""; EXE=""
if [ "$S" = VT ]; then EXE=$EXE_BVT; extra="option.CheckExtensionDepth=8 option.LmrGiveCheck=0 option.LmrInCheck=0 option.LmrFine=1 option.LmrFineHistory=1 option.LmrGiveCheckF=0 option.LmrInCheckF=0"; fi
if [ "$S" = VP ]; then EXE=$EXE_BVP; extra="option.CheckExtensionDepth=8 option.LmrGiveCheck=0 option.LmrInCheck=0 option.SoundPvArm=1 option.SoundStepMask=1"; fi
if [ "$S" = N0 ]; then EXE=$EXE_BVT; extra=""; fi
CMD="/tmp/fastchess/fastchess -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $S14 $extra -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $S14 -each proto=uci nodes=$NODES -openings file=/tmp/evid/openings_queue3.epd format=epd order=sequential start=$START -srand $SEED -rounds 1000 -games 2 -repeat -concurrency 4 -recover -ratinginterval 100 -pgnout file=$M.pgn min=true"
GOT=$(printf '%s' "$CMD" | grep -o 'nodes=[0-9]*' | sort -u | tr '\n' ' ')
GOTSTART=$(printf '%s' "$CMD" | grep -o 'start=[0-9]*' | sort -u | tr '\n' ' ')
if [ "$GOT" != "nodes=$NODES " ] || [ "$GOTSTART" != "start=$START " ]; then
  echo "READBACK FAILED: expected nodes=$NODES start=$START; got: $GOT $GOTSTART - ABORTED" >&2
  exit 1
fi
JJ=/agent/repos/dwqww/forge-combo29/tests_glmflash5_queue3
printf '%s\n' "$CMD" > "$JJ/cmd_$M.txt"
echo "$(date -u +%FT%TZ) cmd_$M.txt written (readback OK: $GOT $GOTSTART; setting $S); launching $M" >> "$JJ/stamps.txt"
t0=$(date -u +%s)
eval "$CMD" > /tmp/evid/${M}_stdout.txt 2>&1
rc=$?
echo "$(date -u +%FT%TZ) $M finished rc=$rc after $(( $(date -u +%s) - t0 ))s" >> "$JJ/stamps.txt"
tail -8 /tmp/evid/${M}_stdout.txt
