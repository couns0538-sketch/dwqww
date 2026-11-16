#!/bin/bash
cd /tmp/g3job2/matches || exit 1
mkdir -p /tmp/g3job2/matches
FC=/tmp/g3job2/fastchess/fastchess 2>/dev/null || true
[ -e "$FC" ] || FC=/tmp/g3job1/fastchess/fastchess
ENG=/tmp/g3job2/build-mag/forge
STOP=$(date -d '2026-11-16 01:39:15 UTC' +%s)
RESERVE=420
EIGHT="option.LmrDeeperShallower=true option.ThreatHistory=true option.NullThreatVerify=true option.NullSeeVeto=true option.ContHist4PlyRead=true option.AspCappedReopen=true option.NonPawnCorrection=true option.MateAlphaGuard=true"

match() { # NAME GAMES SEED DEADLINE CAND_OPTS BASE_OPTS NODES
  echo "$(date -u +%FT%TZ) $(date -u +%s) START match $1 games=$2 seed=$3 deadline=$4 cand=[$5] base=[$6] nodes=$7" >> ../stamps.txt
  local ROUNDS=$(($2 / 2))
  timeout -s INT -k 120 "$4" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $5 \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $6 \
    -each proto=uci nodes=$7 -openings file=/tmp/g3job1/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$3" -rounds "$ROUNDS" -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file="$1.pgn" min=true > "$1.out" 2>&1
  echo "$(date -u +%FT%TZ) $(date -u +%s) END match $1 rc=$?" >> ../stamps.txt
  touch "$1.done"
}

echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
T0=$(date +%s)
timeout -s INT -k 120 300 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=80000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=40000 \
  -each proto=uci -openings file=/tmp/g3job1/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 8200 -rounds 50 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c10.pgn min=true > c10.out 2>&1
T1=$(date +%s); ELAPSED_C=$((T1 - T0)); [ "$ELAPSED_C" -lt 30 ] && ELAPSED_C=30
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$? elapsed=$ELAPSED_C" >> ../stamps.txt
touch c10.done
RATE_C80=$(python3 -c "print(f'{100/$ELAPSED_C:.3f}')")
RATE_Z=$(python3 -c "print(f'{100/$ELAPSED_C*0.75:.3f}')")
echo "$(date -u +%FT%TZ) $(date -u +%s) rate_C80=$RATE_C80 rate_Z_est=$RATE_Z games_per_s" >> ../stamps.txt

Z_NEED=$(python3 -c "print(int(700/$RATE_Z)+90)")
LEFT=$(python3 -c "print(int($STOP - $T1 - $RESERVE))")
if [ "$LEFT" -ge $((2 * Z_NEED)) ]; then
  Z_LIMIT=$Z_NEED
else
  Z_LIMIT=$(python3 -c "print(max(240, $LEFT // 2))")
  echo "$(date -u +%FT%TZ) $(date -u +%s) equal-shares mode: Z_LIMIT=$Z_LIMIT (need was $Z_NEED)" >> ../stamps.txt
fi

/tmp/g3job2/probe10.sh z1 "$EIGHT" "" >/dev/null
match z1 700 8201 "$Z_LIMIT" "$EIGHT" "" 80000
NOW=$(date +%s); Z2=$(python3 -c "print(int($STOP - $NOW - $RESERVE))"); [ "$Z2" -lt 240 ] && Z2=240
[ "$Z2" -gt "$Z_LIMIT" ] && Z2=$Z_LIMIT
/tmp/g3job2/probe10.sh z2 "$EIGHT" "" >/dev/null
match z2 700 8202 "$Z2" "$EIGHT" "" 80000
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
