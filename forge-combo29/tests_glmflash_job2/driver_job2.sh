#!/bin/bash
# glmflash job2 driver: determinism check + M3-M7, fixed 20000 nodes, Hash 16 pinned on both sides.
cd /tmp/glmflash
EXE_B1=/tmp/forge_engine/build/forge
EXE_BND68=/tmp/forge_bnd68/build/forge
EXE_PACKC28=/tmp/forge_packc28/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
WRAP=/tmp/glmflash/wrap_engine_M3.sh
mkdir -p matches2
STOP=$(date -d '+64 minutes' +%s)   # absolute stop; last match takes the cut

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

run_match() {
  local tag=$1 seed=$2 rounds=$3 cand_cmd=$4 base_cmd=$5 limit=$6; shift 6
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 60 ]; then stamp "skip $tag (remaining ${remaining}s < 60s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds cand_cmd=$cand_cmd base_cmd=$base_cmd limit=${limit}s args=($*)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$cand_cmd name=cand "$@" option.Threads=1 option.Hash=16 \
    -engine cmd=$base_cmd name=base option.Threads=1 option.Hash=16 \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches2/$tag.pgn min=true \
    > matches2/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches2/$tag.out > matches2/${tag}_last40.txt
}

# Determinism check: base vs base (B1 exe, no search options), 100 games, limit 150s
run_match D1 7000 50 $EXE_B1 $EXE_B1 150
# M3: B1, HistRework=2, 1500 games, cand wrapped for the input-log proof
run_match M3 7103 750 $WRAP $EXE_B1 720 option.HistRework=2
# M4: B1, TtPruneV2=true, 1500 games
run_match M4 7104 750 $EXE_B1 $EXE_B1 720 option.TtPruneV2=true
# M5: B1, CuckooRep=true, 1500 games
run_match M5 7105 750 $EXE_B1 $EXE_B1 720 option.CuckooRep=true
# M6: bnd68 with its six options, both sides bnd68
run_match M6 7121 1000 $EXE_BND68 $EXE_BND68 1020 option.NonPawnCorr=1 option.PawnHist=1 option.NonPawnCorrWeight=50 option.ContHist4Pct=45 option.EvalOnlyStore=1 option.EvalOnlyStoreMinDepth=2
# M7: packc28 with its four options, both sides packc28 (takes whatever is left; expected cut)
run_match M7 7122 1000 $EXE_PACKC28 $EXE_PACKC28 20000 option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3 option.EvalSwingMult=24 option.EvalSwingMax=200
stamp "driver2 done"
