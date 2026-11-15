#!/bin/sh
# One match: $1=name $2=option-string $3=seed $4=rounds
NAME=$1; OPT=$2; SEED=$3; ROUNDS=$4
EXE=/tmp/ds/build-job9/forge
/tmp/fastchess/fastchess \
  -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 $OPT \
  -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 \
  -each proto=uci nodes=20000 \
  -openings file=/tmp/ds/book/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand $SEED -rounds $ROUNDS -games 2 -repeat \
  -concurrency 4 -recover -ratinginterval 1000 \
  -pgnout file=/tmp/ds/job9/$NAME.pgn min=true \
  > /tmp/ds/job9/$NAME.log 2>&1
