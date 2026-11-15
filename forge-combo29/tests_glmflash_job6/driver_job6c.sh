#!/bin/bash
# glmflash job6 driver C: matches only. The four probes already ran (driver6b) and their
# tee'd input logs prove delivery of option.CorrMargin (x2 each); the 1-pair shape check
# is recorded, not gated (job-4 lesson: one pair cannot prove non-degeneracy).
cd /tmp/glmflash
EXE=/tmp/forge_cm/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+42 minutes' +%s)
mkdir -p matches6

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

run_match() {
  local tag=$1 seed=$2 rounds=$3 limit=$4; shift 4
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds limit=${limit}s args=($*)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false "$@" \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches6/$tag.pgn min=true \
    > matches6/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches6/$tag.out > matches6/${tag}_last40.txt
  stamp "warn $tag count=$(grep -c "doesn't have option" matches6/$tag.out)"
  stamp "shape $tag $(python3 /tmp/glmflash/pairshape.py matches6/$tag.pgn cand | head -1)"
}

run_match M1 7161 1000 975 option.CorrMargin=24
run_match M3 7163 1000 975 option.CorrMargin=64
run_match M2 7162 1000 975 option.CorrMargin=24
run_match M4 7164 1000 975 option.CorrMargin=64
stamp "driver6c done"
