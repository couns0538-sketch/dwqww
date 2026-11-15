#!/bin/bash
# Job 2 matches, chained: control C first (power line), then M1 and M2 (the two
# prescribed 2000-game seeds). Each match has its own deadline; the last one is
# the one that would be cut. rounds = games/2 computed by run_match2.sh.
cd /tmp/g3job2/matches || exit 1
FC=/tmp/g3job2/fastchess/fastchess
ENG=/tmp/g3job2/build-patched/forge

echo "$(date -u +%FT%TZ) $(date -u +%s) START control C" >> ../stamps.txt
timeout -s INT -k 120 240 "$FC" \
  -engine cmd="$ENG" name=fast option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd="$ENG" name=slow option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci -openings file=/tmp/g3job2/UHO_Lichess_4852_v1.epd format=epd order=random \
  -srand 7600 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=c.pgn min=true > c.out 2>&1
echo "$(date -u +%FT%TZ) $(date -u +%s) END control C rc=$?" >> ../stamps.txt
touch c.done

/tmp/g3job2/run_match2.sh m1 1050 2000 7601 "option.PawnHistory=true" "" > m1_run.log 2>&1
touch m1.done

/tmp/g3job2/run_match2.sh m2 1050 2000 7602 "option.PawnHistory=true" "" > m2_run.log 2>&1
touch m2.done
echo "$(date -u +%FT%TZ) $(date -u +%s) ALL MATCHES DONE" >> ../stamps.txt
