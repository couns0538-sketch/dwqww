#!/bin/bash
# deepseek job13 driver B: M1 and M3 only (their probes died on the dash sentinel; M2/M4 are done).
cd /tmp/glmflash
EXE=/tmp/ds13_o1/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+40 minutes' +%s)
mkdir -p matches_ds13

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

probe() {
  local tag=$1 seed=$2 cand_extra=$3
  local wp=/tmp/glmflash/matches_ds13/wp_$tag.sh
  { echo '#!/bin/sh'; echo "exec tee -a /tmp/glmflash/matches_ds13/probe_${tag}_uci_in.log | exec $EXE"; } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_extra nodes=20000 \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
    -each proto=uci \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches_ds13/probe_$tag.pgn min=true \
    > matches_ds13/probe_$tag.out 2>&1
  stamp "probe $tag pairshape=$(python3 /tmp/glmflash/pairshape.py matches_ds13/probe_$tag.pgn cand | head -1) (recorded)"
  local ok=1 line name value n
  for uci_line in $cand_extra; do
    name=$(echo "$uci_line" | sed -n 's/option\.\([A-Za-z0-9]*\)=.*/\1/p')
    value=$(echo "$uci_line" | sed -n 's/.*=\(.*\)$/\1/p')
    line="setoption name $name value $value"
    n=$(grep -cF "$line" /tmp/glmflash/matches_ds13/probe_${tag}_uci_in.log 2>/dev/null || echo 0)
    stamp "probe $tag delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done
  if [ "$ok" = "1" ]; then stamp "probe OK $tag"; return 0; else stamp "PROBEFAIL $tag"; return 1; fi
}

run_match() {
  local tag=$1 seed=$2 rounds=$3 limit=$4 cand_opts=$5
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds limit=${limit}s cand=($cand_opts) base=()"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_opts \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches_ds13/$tag.pgn min=true \
    > matches_ds13/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches_ds13/$tag.out > matches_ds13/${tag}_last40.txt
  stamp "warn $tag count=$(grep -c "doesn't have option" matches_ds13/$tag.out)"
  stamp "shape $tag $(python3 /tmp/glmflash/pairshape.py matches_ds13/$tag.pgn cand | head -1)"
}

if probe M1 8501 "option.PawnHistory=true option.ContHistDeep=1"; then run_match M1 7401 1000 930 "option.PawnHistory=true option.ContHistDeep=1"; else stamp "skip M1 (probe failed)"; fi
if probe M3 8503 "option.PawnHistory=true option.ContHistDeep=1"; then run_match M3 7403 1000 930 "option.PawnHistory=true option.ContHistDeep=1"; else stamp "skip M3 (probe failed)"; fi
stamp "driver_ds13b done"
