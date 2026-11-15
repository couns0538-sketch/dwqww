#!/bin/bash
cd /tmp/g3job8/matches || exit 1
FC=/tmp/g3job8/fastchess/fastchess
ENG=/tmp/g3job8/build-patched/forge
STOP=$(date -d '2026-11-16 00:03:30 UTC' +%s)
RESERVE=420

match() { # NAME GAMES SEED DEADLINE CAND_OPTS
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 deadline=$4 cand=[$5]" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 -openings file=/tmp/g3job8/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$3" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file="$1.pgn" min=true > "$1.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) END match $1 rc=$?" >> ../stamps.txt
  touch "$1.done"
}

echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
timeout -s INT -k 120 260 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job8/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 8200 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c.pgn min=true > c.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c.done

S1=$(( (STOP - $(date +%s) - RESERVE) / 4 )); [ "$S1" -lt 300 ] && S1=300

/tmp/g3job8/probe8.sh m1 "option.NullMoveHanging=1" >/dev/null
match m1 2000 8201 "$S1" "option.NullMoveHanging=1"
/tmp/g3job8/probe8.sh m2 "option.NullMoveHanging=1" >/dev/null
match m2 2000 8202 "$S1" "option.NullMoveHanging=1"
/tmp/g3job8/probe8.sh m3 "option.NullMoveHanging=2" >/dev/null
match m3 2000 8203 "$S1" "option.NullMoveHanging=2"
NOW=$(date +%s); S4=$((STOP - NOW - RESERVE)); [ "$S4" -lt 300 ] && S4=300
/tmp/g3job8/probe8.sh m4 "option.NullMoveHanging=2" >/dev/null
match m4 2000 8204 "$S4" "option.NullMoveHanging=2"
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
