#!/bin/bash
cd /tmp/g3job8/matches || exit 1
FC=/tmp/g3job8/fastchess/fastchess
ENG=/tmp/g3job8/build-patched/forge
STOP=$(date -d '2026-11-16 01:05:40 UTC' +%s)
RESERVE=480

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 deadline=$4 cand=[$5] base=[$6]" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
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
  -srand 8210 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c9.pgn min=true > c9.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c9.done

/tmp/g3job8/probe8.sh x1 "option.NullThreatVerify=true" "" >/dev/null
match x1 2000 8211 950 "option.NullThreatVerify=true" ""
/tmp/g3job8/probe8.sh x2 "option.NullSeeVeto=true" "" >/dev/null
match x2 2000 8212 950 "option.NullSeeVeto=true" ""
/tmp/g3job8/probe8.sh x3 "option.NullThreatVerify=true option.NullSeeVeto=true" "" >/dev/null
match x3 2000 8213 950 "option.NullThreatVerify=true option.NullSeeVeto=true" ""
NOW=$(date +%s); X4=$((STOP - NOW - RESERVE)); [ "$X4" -lt 300 ] && X4=0
if [ "$X4" -ge 300 ]; then
  /tmp/g3job8/probe8.sh x4 "option.NullMoveHanging=1" "option.NullThreatVerify=true" >/dev/null
  match x4 2000 8214 "$X4" "option.NullMoveHanging=1" "option.NullThreatVerify=true"
fi
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
