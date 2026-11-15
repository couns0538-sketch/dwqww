#!/bin/bash
cd /tmp/g3job5/matches || exit 1
FC=/tmp/g3job5/fastchess/fastchess
ENG=/tmp/g3job5/build-pk/forge
STOP=$(date -d '2026-11-15 22:10:20 UTC' +%s)
RESERVE=600   # report + commit + push

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

echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
T0=$(date +%s)
timeout -s INT -k 120 260 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 7360 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c6.pgn min=true > c6.out 2>&1
T1=$(date +%s); ELAPSED_C=$((T1 - T0)); [ "$ELAPSED_C" -lt 30 ] && ELAPSED_C=30
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$? elapsed=$ELAPSED_C" >> ../stamps.txt
touch c6.done
RATE_C=$(python3 -c "print(f'{300/$ELAPSED_C:.3f}')")
# job-5 lesson: the 4x factor was ~20% optimistic - correct it (measured 0.511-0.552 in job 5)
RATE_D=$(python3 -c "print(f'{300/$ELAPSED_C/4*0.8:.3f}')")
echo "$(date -u +%FT%TZ) $(date -u +%s) rate_C=$RATE_C rate_D_corrected=$RATE_D games_per_s" >> ../stamps.txt

# E1 and E2 get EQUAL shares of what is left (job text); E4 cut first, then E3 - neither starts
# unless >= 420 s remain after E2.
R1=$((STOP - $(date +%s) - RESERVE))
HALF=$((R1 / 2)); [ "$HALF" -lt 300 ] && HALF=300
E1_LIMIT=$HALF
E2_LIMIT=$HALF

/tmp/g3job5/probe6.sh e1 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "" >/dev/null
match e1 800 7361 "$E1_LIMIT" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" ""

NOW=$(date +%s); R2=$((STOP - NOW - RESERVE)); [ "$R2" -lt "$E2_LIMIT" ] && E2_LIMIT=$R2; [ "$E2_LIMIT" -lt 300 ] && E2_LIMIT=300
/tmp/g3job5/probe6.sh e2 "option.EvalSwingMult=12 option.EvalSwingMax=200" "" >/dev/null
match e2 800 7362 "$E2_LIMIT" "option.EvalSwingMult=12 option.EvalSwingMax=200" ""

NOW=$(date +%s); LEFT3=$((STOP - NOW - 420))
if [ "$LEFT3" -ge 420 ]; then
  /tmp/g3job5/probe6.sh e3 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" "" >/dev/null
  match e3 800 7363 "$LEFT3" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" ""
  NOW=$(date +%s); LEFT4=$((STOP - NOW - 90))
  if [ "$LEFT4" -ge 420 ]; then
    /tmp/g3job5/probe6.sh e4 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "option.EvalSwingMult=12 option.EvalSwingMax=200" >/dev/null
    match e4 800 7364 "$LEFT4" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "option.EvalSwingMult=12 option.EvalSwingMax=200"
  fi
fi
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
