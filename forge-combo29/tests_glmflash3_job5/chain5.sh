#!/bin/bash
cd /tmp/g3job5/matches || exit 1
FC=/tmp/g3job5/fastchess/fastchess
ENG=/tmp/g3job5/build-pk/forge
STOP=$(date -d '2026-11-15 21:27:53 UTC' +%s)
ln -sfn /tmp/g3job1/UHO_Lichess_4852_v1.epd /tmp/g3job5/UHO_Lichess_4852_v1.epd

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS NODES
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 deadline=$4 cand=[$5] base=[$6] nodes=$7" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
    -each proto=uci nodes=$7 -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
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
  -srand 7350 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c.pgn min=true > c.out 2>&1
T1=$(date +%s)
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$? elapsed=$((T1-T0))" >> ../stamps.txt
touch c.done
# rate from C: games/s of the 20000/10000 mix; an 80000-node game ~ 4x one of C's (job text)
ELAPSED_C=$((T1 - T0)); [ "$ELAPSED_C" -lt 30 ] && ELAPSED_C=30
RATE_C=$(python3 -c "print(f'{300/$ELAPSED_C:.3f}')")
RATE_D=$(python3 -c "print(f'{300/$ELAPSED_C/4:.3f}')")
echo "$(date -u +%FT%TZ) $(date -u +%s) rate_C=$RATE_C rate_D=$RATE_D games_per_s" >> ../stamps.txt

# D1 and D2 get equal shares of what is left after C (minus report reserve)
LEFT=$(python3 -c "print(int($STOP - $T1 - 540))")
HALF=$(python3 -c "print(max(300, $LEFT // 2))")
D1_LIMIT=$HALF; D2_LIMIT=$HALF

/tmp/g3job5/probe5.sh d1 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" "" >/dev/null
match d1 800 7351 "$D1_LIMIT" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3" "" 80000

NOW=$(date +%s); LEFT2=$(python3 -c "print(int($STOP - $NOW - 540))")
[ "$LEFT2" -lt "$D2_LIMIT" ] && D2_LIMIT=$LEFT2
[ "$D2_LIMIT" -lt 300 ] && D2_LIMIT=300
/tmp/g3job5/probe5.sh d2 "option.EvalSwingMult=12 option.EvalSwingMax=200" "" >/dev/null
match d2 800 7352 "$D2_LIMIT" "option.EvalSwingMult=12 option.EvalSwingMax=200" "" 80000

NOW=$(date +%s); LEFT3=$(python3 -c "print(int($STOP - $NOW - 420))")
if [ "$LEFT3" -ge 420 ]; then
  /tmp/g3job5/probe5.sh d3 "option.EvalSwingMult=24 option.EvalSwingMax=200" "" >/dev/null
  match d3 800 7353 "$LEFT3" "option.EvalSwingMult=24 option.EvalSwingMax=200" "" 80000
  NOW=$(date +%s); LEFT4=$(python3 -c "print(int($STOP - $NOW - 90))")
  if [ "$LEFT4" -ge 420 ]; then
    /tmp/g3job5/probe5.sh d4 "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "" >/dev/null
    match d4 800 7354 "$LEFT4" "option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=12 option.EvalSwingMax=200" "" 80000
  fi
fi
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
