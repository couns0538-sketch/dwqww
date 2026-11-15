#!/bin/bash
# glmflash job3 driver: wrapper-bench checks then M6, M7, M8, M9 (2000 nodes... fixed 20000 nodes), Hash 16 both sides.
cd /tmp/glmflash
EXE_B1=/tmp/forge_engine/build/forge
EXE_BND68=/tmp/forge_bnd68/build/forge
EXE_PACKC28=/tmp/forge_packc28/build/forge
EXE_PACKA=/tmp/forge_packa/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
WRAP_BND68=/tmp/glmflash/wrap_bnd68.sh
WRAP_PACKC28=/tmp/glmflash/wrap_packc28.sh
WRAP_PACKA=/tmp/glmflash/wrap_packa.sh
mkdir -p matches3
STOP=$(date -d '+66 minutes' +%s)   # absolute stop; M9 (last) takes the cut

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

# check 1 per wrapper: bench 13 through the wrapper must print the expected ON number
wrap_check() {
  local tag=$1 wrap=$2 expect=$3 exe=$4
  local got
  got=$(printf 'uci\nbench 13\nquit\n' | timeout 120 "$wrap" 2>&1 | grep -oE "bench depth 13 nodes [0-9]+" | grep -oE "[0-9]+$")
  if [ "$got" = "$expect" ]; then stamp "wrapcheck $tag PASS ($got)"; return 0; else stamp "wrapcheck $tag FAIL (got ${got:-none}, expected $expect)"; return 1; fi
}

run_match() {
  local tag=$1 seed=$2 rounds=$3 cand_cmd=$4 base_cmd=$5 limit=$6; shift 6
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds cand_cmd=$cand_cmd base_cmd=$base_cmd limit=${limit}s args=($*)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$cand_cmd name=cand option.Threads=1 option.Hash=16 "$@" \
    -engine cmd=$base_cmd name=base option.Threads=1 option.Hash=16 \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches3/$tag.pgn min=true \
    > matches3/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches3/$tag.out > matches3/${tag}_last40.txt
  local w=$(grep -c "doesn't have option" matches3/$tag.out)
  stamp "warn $tag count=$w"
}

# M6: bnd68 via wrapper, 2000 games
if wrap_check M6 $WRAP_BND68 776194; then
  run_match M6 7131 1000 $WRAP_BND68 $EXE_BND68 990
else
  stamp "skip M6 (wrapcheck failed)"
fi
# M7: packc28 via wrapper, 2000 games
if wrap_check M7 $WRAP_PACKC28 690187; then
  run_match M7 7132 1000 $WRAP_PACKC28 $EXE_PACKC28 990
else
  stamp "skip M7 (wrapcheck failed)"
fi
# M8: packa via wrapper (its three options are undeclared; wrapper bench check passed pre-launch)
if wrap_check M8 $WRAP_PACKA 744597; then
  run_match M8 7133 1000 $WRAP_PACKA $EXE_PACKA 990
else
  stamp "skip M8 (wrapcheck failed)"
fi
# M9: B1, HistRework=2 (declared), 2000 games — takes whatever is left; expected cut
run_match M9 7134 1000 $EXE_B1 $EXE_B1 20000 option.HistRework=2
stamp "driver3 done"
