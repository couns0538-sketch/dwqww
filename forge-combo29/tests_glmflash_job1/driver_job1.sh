#!/bin/bash
# glmflash job1 driver: controls C1-C3 then matches M1-M5, fixed nodes, no clock.
cd /tmp/glmflash
EXE=/tmp/forge_engine/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
WRAP=/tmp/glmflash/wrap_engine.sh
mkdir -p matches
DEADLINE=$(date -d '+46 minutes' +%s)   # stop starting new matches after 46 min; interrupt running ones at their timeout

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

run_match() {
  local tag=$1 seed=$2 rounds=$3 cand_cmd=$4; shift 4
  local remaining=$(( DEADLINE - $(date +%s) ))
  if [ "$remaining" -lt 180 ]; then stamp "skip $tag (remaining ${remaining}s < 180s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds cand_cmd=$cand_cmd args=($*)"
  timeout -s INT --kill-after=20 "$remaining" $FC \
    -engine cmd=$cand_cmd name=cand "$@" \
    -engine cmd=$EXE name=base \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches/$tag.pgn min=true \
    > matches/$tag.out 2>&1
  stamp "end $tag exit=$? sig=$?"
  tail -40 matches/$tag.out > matches/${tag}_last40.txt
}

# Control 1: tool fairness, base vs base, no options, 600 games
run_match C1 7001 300 $EXE
# Control 2: cand nodes=20000 vs base nodes=10000, no options, 300 games (per-engine nodes)
stamp "start C2"
timeout -s INT --kill-after=20 $(( DEADLINE - $(date +%s) )) $FC \
  -engine cmd=$EXE name=cand nodes=20000 \
  -engine cmd=$EXE name=base nodes=10000 \
  -each proto=uci \
  -openings file=$BOOK format=epd order=random \
  -srand 7002 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=matches/C2.pgn min=true \
  > matches/C2.out 2>&1
stamp "end C2 exit=$?"
tail -40 matches/C2.out > matches/C2_last40.txt

# Control 3: 2-game match, option.BundlePreset=B1, wrapper tees cand's UCI input to a log
stamp "start C3"
timeout -s INT --kill-after=20 300 $FC \
  -engine cmd=$WRAP name=cand option.BundlePreset=B1 \
  -engine cmd=$EXE name=base \
  -each proto=uci nodes=20000 \
  -openings file=$BOOK format=epd order=random \
  -srand 7003 -rounds 1 -games 2 -repeat -concurrency 2 -recover \
  -ratinginterval 100 -pgnout file=matches/C3.pgn min=true \
  > matches/C3.out 2>&1
stamp "end C3 exit=$?"
tail -40 matches/C3.out > matches/C3_last40.txt

# M1: BundlePreset=B1 vs base, 3000 games, seed 7101
run_match M1 7101 1500 $EXE option.BundlePreset=B1
# M2: HistRework=2 CuckooRep=true TtPruneV2=true vs base, 2000 games, seed 7102
run_match M2 7102 1000 $EXE option.HistRework=2 option.CuckooRep=true option.TtPruneV2=true
# M3: HistRework=2 vs base, 1500 games, seed 7103
run_match M3 7103 750 $EXE option.HistRework=2
# M4: TtPruneV2=true vs base, 1500 games, seed 7104
run_match M4 7104 750 $EXE option.TtPruneV2=true
# M5: CuckooRep=true vs base, 1500 games, seed 7105
run_match M5 7105 750 $EXE option.CuckooRep=true
stamp "driver done"
