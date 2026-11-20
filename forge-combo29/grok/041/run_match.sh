#!/usr/bin/env bash
# Match IdeaK2 on (k2on) against IdeaK2 off (k2off). Both are exe P.
# S14, Threads 1, Hash 16, OwnBook false, 20000 nodes a move.
# rounds = number of openings; games 2 = both colours.
# concurrency = nproc - 1.
set -u
EXE="$1"
OPENINGS="$2"
OUTDIR="$3"
ROUNDS="$4"
mkdir -p "$OUTDIR"
cd "$OUTDIR"
CORES=$(nproc)
CONC=$((CORES - 1))
if [ "$CONC" -lt 1 ]; then CONC=1; fi
echo "concurrency=$CONC rounds=$ROUNDS games=2" | tee run_note.txt
/home/ubuntu/fastchess/fastchess \
  -engine cmd="$EXE" name=k2on proto=uci option.IdeaK2=true option.IdeaK2_Plies=4 \
  -engine cmd="$EXE" name=k2off proto=uci option.IdeaK2=false option.IdeaK2_Plies=4 \
  -each nodes=20000 option.Threads=1 option.Hash=16 option.OwnBook=false \
    option.LmrQuietBase=93 option.LmrQuietDivisor=205 option.LmrNoisyBase=13 \
    option.LmrNoisyDivisor=333 option.LmrHistoryDivisor=5643 option.NullMoveBase=5 \
    option.LmpBase=8 option.HistoryPruneMultiplier=2220 option.HistoryBonusQuadratic=24 \
    option.HistoryBonusLinear=54 option.HistoryBonusMax=2212 option.SingularDepth=6 \
    option.IirDepth=2 option.NonPawnCorrection=true \
  -openings "file=$OPENINGS" format=epd order=sequential \
  -rounds "$ROUNDS" -games 2 -concurrency "$CONC" \
  -pgnout file=games.pgn notation=uci min=true \
  -ratinginterval 100 \
  -config outname=fastchess_config.json \
  > match.log 2>&1
echo "fastchess_exit=$?" | tee -a run_note.txt
tail -n 30 match.log
