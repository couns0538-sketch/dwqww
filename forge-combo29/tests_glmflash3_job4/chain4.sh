#!/bin/bash
cd /tmp/g3job4/matches || exit 1
FC=/tmp/g3job4/fastchess/fastchess
ENG=/tmp/g3job4/build-b1tree/forge
STOP=$(date -d '2026-11-15 20:19:48 UTC' +%s)

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 cand=[$5] base=[$6]" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
    -each proto=uci nodes=20000 -openings file=/tmp/g3job4/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$3" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file="$1.pgn" min=true > "$1.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) END match $1 rc=$?" >> ../stamps.txt
  touch "$1.done"
}

echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
timeout -s INT -k 120 260 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job4/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 7620 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c.pgn min=true > c.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c.done

/tmp/g3job4/probe4.sh m1 "option.BundlePreset=B1 option.PawnHistory=true" "option.BundlePreset=B1" >/dev/null
match m1 2000 7621 1000 "option.BundlePreset=B1 option.PawnHistory=true" "option.BundlePreset=B1"

/tmp/g3job4/probe4.sh m3 "option.PawnHistory=true" "" >/dev/null
match m3 2000 7623 1000 "option.PawnHistory=true" ""

/tmp/g3job4/probe4.sh m2 "option.BundlePreset=B1 option.PawnHistory=true" "option.BundlePreset=B1" >/dev/null
NOW=$(date +%s); LEFT=$((STOP - NOW - 90)); [ "$LEFT" -gt 1000 ] && LEFT=1000
match m2 2000 7622 "$LEFT" "option.BundlePreset=B1 option.PawnHistory=true" "option.BundlePreset=B1"
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
