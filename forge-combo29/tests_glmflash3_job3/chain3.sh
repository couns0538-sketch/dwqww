#!/bin/bash
# Job 3 matches: probe first, then the match; per-match deadlines; M5 only if
# the clock allows (stop-and-write epoch 1794768828 minus margin).
cd /tmp/g3job3/matches || exit 1
FC=/tmp/g3job3/fastchess/fastchess
ENG=/tmp/g3job3/build-v2/forge
STOP=1794768828

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 cand=[$5] base=[$6]" >> ../stamps.txt
  local ROUNDS=$((2 / 1 * $2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
    -each proto=uci nodes=20000 -openings file=/tmp/g3job3/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$3" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file="$1.pgn" min=true > "$1.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) END match $1 rc=$?" >> ../stamps.txt
  touch "$1.done"
}

/tmp/g3job3/probe.sh C "nodes=20000" "nodes=10000" >/dev/null
echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
timeout -s INT -k 120 200 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job3/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 7610 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c.pgn min=true > c.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c.done

/tmp/g3job3/probe.sh m1 "option.PawnHistory=true option.PawnHistoryBits=10" "" >/dev/null
match m1 2000 7611 900 "option.PawnHistory=true option.PawnHistoryBits=10" ""

/tmp/g3job3/probe.sh m2 "option.PawnHistory=true option.PawnHistoryBits=9" "" >/dev/null
match m2 2000 7612 900 "option.PawnHistory=true option.PawnHistoryBits=9" ""

/tmp/g3job3/probe.sh m3 "option.PawnHistory=true option.PawnHistoryPvBonus=1" "" >/dev/null
match m3 2000 7613 900 "option.PawnHistory=true option.PawnHistoryPvBonus=1" ""

/tmp/g3job3/probe.sh m4 "option.PawnHistory=true option.PawnHistoryBits=10" "option.PawnHistory=true option.PawnHistoryBits=12" >/dev/null
match m4 2000 7614 900 "option.PawnHistory=true option.PawnHistoryBits=10" "option.PawnHistory=true option.PawnHistoryBits=12"

NOW=$(date +%s)
LEFT=$((STOP - NOW - 90))
if [ "$LEFT" -ge 420 ]; then
  /tmp/g3job3/probe.sh m5 "option.PawnHistory=true option.PawnHistoryWeight=50" "" >/dev/null
  match m5 1500 7615 "$LEFT" "option.PawnHistory=true option.PawnHistoryWeight=50" ""
fi
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
