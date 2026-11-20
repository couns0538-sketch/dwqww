#!/usr/bin/env bash
# Fixed-node match. OwnBook is forced off: the engine's default book is on and
# would play moves without searching. S14 is sent to both engines. The only
# difference is IdeaS15.
set -u
SEAT=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$SEAT"
EXE="${1:?exe}"
ROUNDS="${2:?rounds}"
OPENINGS="${3:?openings}"
LOG="${4:?log}"
PGN="${5:?pgn}"
ON_NAME="${6:-S15on}"
OFF_NAME="${7:-S15off}"
ON_OPT="${8:-option.IdeaS15=true}"
OFF_OPT="${9:-option.IdeaS15=false}"
cd "$DIR"
/tmp/fastchess/fastchess \
  -concurrency 3 \
  -rounds "$ROUNDS" \
  -games 2 \
  -openings "file=${OPENINGS}" format=epd order=sequential \
  -each proto=uci nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -engine "cmd=${EXE}" "name=${ON_NAME}" "${ON_OPT}" \
  -engine "cmd=${EXE}" "name=${OFF_NAME}" "${OFF_OPT}" \
  -pgnout "file=${PGN}" notation=uci min=true \
  -ratinginterval 100 \
  > "$LOG" 2>&1
echo "match exit $? log $LOG"
tail -n 30 "$LOG"
