#!/bin/bash
# usage: probe.sh NAME "CAND_OPTS" "BASE_OPTS" [PER_ENGINE_NODES]
# 2-game probe with the engine input log on; extracts the setoption lines both
# sides received into probe_$NAME.txt. Run before every match, same command shape.
NAME="$1"; CAND_OPTS="$2"; BASE_OPTS="$3"; NODES_SPEC="$4"
cd /tmp/g3job5/matches || exit 1
FC=/tmp/g3job5/fastchess/fastchess
ENG=/tmp/g3job5/build-pk/forge
if [ -n "$NODES_SPEC" ]; then
  timeout -s INT -k 60 120 "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $CAND_OPTS $NODES_SPEC \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $BASE_OPTS \
    -each proto=uci -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand 7699 -rounds 1 -games 2 -repeat -concurrency 1 -recover \
    -log file=probe_$NAME.log level=trace engine=true append=false \
    -ratinginterval 100 -pgnout file=probe_$NAME.pgn min=true > probe_$NAME.out 2>&1
else
  timeout -s INT -k 60 120 "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $CAND_OPTS \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $BASE_OPTS \
    -each proto=uci nodes=20000 -openings file=/tmp/g3job5/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand 7699 -rounds 1 -games 2 -repeat -concurrency 1 -recover \
    -log file=probe_$NAME.log level=trace engine=true append=false \
    -ratinginterval 100 -pgnout file=probe_$NAME.pgn min=true > probe_$NAME.out 2>&1
fi
{ echo "== probe $NAME: cand side setoption lines =="; grep 'cand <--- setoption' probe_$NAME.log | sed 's/.*cand <--- //';
  echo "== probe $NAME: base side setoption lines =="; grep 'base <--- setoption' probe_$NAME.log | sed 's/.*base <--- //'; } > probe_$NAME.txt
echo "$(date -u +%FT%TZ) $(date -u +%s) probe $NAME done" >> ../stamps.txt
cat probe_$NAME.txt
