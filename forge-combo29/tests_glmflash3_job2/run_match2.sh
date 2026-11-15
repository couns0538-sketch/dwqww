#!/bin/bash
# usage: run_match2.sh NAME DEADLINE_S GAMES SEED "CAND_OPTS" "BASE_OPTS"
# The prescribed match form; rounds = GAMES/2 is COMPUTED here, never hand-typed
# (the job-1 lesson). SIGINT at the deadline ends a cut match; its finished games count.
NAME="$1"; DEADLINE="$2"; GAMES="$3"; SEED="$4"; CAND_OPTS="$5"; BASE_OPTS="$6"
ROUNDS=$((GAMES / 2))
cd /tmp/g3job2/matches || exit 1
echo "$(date -u +%FT%TZ) $(date -u +%s) START match $NAME games=$GAMES seed=$SEED cand=[$CAND_OPTS] base=[$BASE_OPTS]" >> ../stamps.txt
timeout -s INT -k 120 "$DEADLINE" /tmp/g3job2/fastchess/fastchess \
  -engine cmd=/tmp/g3job2/build-patched/forge name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $CAND_OPTS \
  -engine cmd=/tmp/g3job2/build-patched/forge name=base option.Threads=1 option.Hash=16 option.OwnBook=false $BASE_OPTS \
  -each proto=uci nodes=20000 -openings file=/tmp/g3job2/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand "$SEED" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout "file=$NAME.pgn" min=true > "$NAME.out" 2>&1
RC=$?
echo "$(date -u +%FT%TZ) $(date -u +%s) END match $NAME rc=$RC" >> ../stamps.txt
tail -12 "$NAME.out"
