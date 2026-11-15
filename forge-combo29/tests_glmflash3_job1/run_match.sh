#!/bin/bash
# usage: run_match.sh NAME DEADLINE_S ROUNDS SEED "CAND_OPTS" "BASE_OPTS"
# The match form is the one prescribed in FABLE_TO_glmflash3_1.md; the only freedom
# given by the job is <option.NAME=VALUE ...> per side. SIGINT at the deadline ends a
# cut match so its finished games count (fastchess marks them INCOMPLETE).
NAME="$1"; DEADLINE="$2"; ROUNDS="$3"; SEED="$4"; CAND_OPTS="$5"; BASE_OPTS="$6"
cd /tmp/g3job1/matches || exit 1
echo "$(date -u +%FT%TZ) $(date -u +%s) START match $NAME rounds=$ROUNDS seed=$SEED cand=[$CAND_OPTS] base=[$BASE_OPTS]" >> ../stamps.txt
timeout -s INT -k 120 "$DEADLINE" /tmp/g3job1/fastchess/fastchess \
  -engine cmd=/tmp/g3job1/build/forge name=cand option.Threads=1 option.Hash=16 $CAND_OPTS \
  -engine cmd=/tmp/g3job1/build/forge name=base option.Threads=1 option.Hash=16 $BASE_OPTS \
  -each proto=uci nodes=20000 -openings file=/tmp/g3job1/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand "$SEED" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout "file=$NAME.pgn" min=true > "$NAME.out" 2>&1
RC=$?
echo "$(date -u +%FT%TZ) $(date -u +%s) END match $NAME rc=$RC" >> ../stamps.txt
tail -12 "$NAME.out"
