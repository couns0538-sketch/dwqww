#!/bin/bash
cd /tmp/g3job5/matches || exit 1
FC=/tmp/g3job5/fastchess/fastchess
ENG=/tmp/g3job5/build-pk/forge
STOP=$(date -d '2026-11-15 22:55:20 UTC' +%s)
RESERVE=420

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 deadline=$4 cand=[$5] base=[$6]" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
    -each proto=uci nodes=80000 -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$3" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file="$1.pgn" min=true > "$1.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) END match $1 rc=$?" >> ../stamps.txt
  touch "$1.done"
}

/tmp/g3job5/probe6.sh c7 "nodes=20000" "nodes=10000" >/dev/null
echo "$(date -u +%FT%TZ) $(date -u +%s) START control C (100 games, rate NOT taken from it)" >> ../stamps.txt
timeout -s INT -k 120 200 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 7370 -rounds 50 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c7.pgn min=true > c7.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c7.done

# F1 to its full 800 games before F2 starts (job text); cap from job 6's measured 0.54 games/s
F1_LIMIT=1600
/tmp/g3job5/probe6.sh f1 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" "" >/dev/null
match f1 800 7363 "$F1_LIMIT" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" ""

NOW=$(date +%s); F2_LIMIT=$((STOP - NOW - RESERVE))
if [ "$F2_LIMIT" -ge 240 ]; then
  /tmp/g3job5/probe6.sh f2 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "option.EvalSwingMult=12 option.EvalSwingMax=200" >/dev/null
  match f2 800 7364 "$F2_LIMIT" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "option.EvalSwingMult=12 option.EvalSwingMax=200"
fi
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
