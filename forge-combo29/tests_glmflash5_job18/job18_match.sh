#!/bin/bash
# Job 18 match driver: builds the exact fastchess command for a match,
# writes it to cmd_<M>.txt BEFORE the match starts, then runs it.
# Usage: job18_match.sh <M> <seed> <start> <nodes> <rounds> <cand_extra_options...>
set -u
M=$1; SEED=$2; START=$3; NODES=$4; ROUNDS=$5; shift 5
CAND_EXTRA="$*"
EXE=/tmp/forgebuild_b6/forge
S14="option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 option.IirDepth=2 option.NonPawnCorrection=true"
CMD="/tmp/fastchess/fastchess -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $S14 $CAND_EXTRA -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $S14 -each proto=uci nodes=$NODES -openings file=/tmp/evid/openings_job18.epd format=epd order=sequential start=$START -srand $SEED -rounds $ROUNDS -games 2 -repeat -concurrency 4 -recover -ratinginterval 100 -pgnout file=$M.pgn min=true"
J=/agent/repos/dwqww/forge-combo29/tests_glmflash5_job18
printf '%s\n' "$CMD" > "$J/cmd_$M.txt"
echo "$(date -u +%FT%TZ) cmd_$M.txt written (exact command); launching $M" >> "$J/stamps.txt"
t0=$(date -u +%s)
eval "$CMD" > /tmp/evid/${M}_stdout.txt 2>&1
rc=$?
echo "$(date -u +%FT%TZ) $M finished rc=$rc after $(( $(date -u +%s) - t0 ))s" >> "$J/stamps.txt"
tail -8 /tmp/evid/${M}_stdout.txt
