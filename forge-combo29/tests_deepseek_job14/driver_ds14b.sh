#!/bin/bash
# deepseek job14 driver B: divisor matches on the node clock (V1, V2, V3).
cd /tmp/glmflash
EXE=/tmp/ds14_nc/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+42 minutes' +%s)
mkdir -p matches_ds14

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

probe() {
  local tag=$1 seed=$2 cand_extra=$3 base_extra=$4
  local wp=/tmp/glmflash/matches_ds14/wp_$tag.sh
  { echo '#!/bin/sh'; echo "exec tee -a /tmp/glmflash/matches_ds14/probe_${tag}_uci_in.log | exec $EXE"; } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.NodeClock=100 $cand_extra \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false option.NodeClock=100 $base_extra \
    -each proto=uci tc=10+0.1 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches_ds14/probe_$tag.pgn min=true \
    > matches_ds14/probe_$tag.out 2>&1
  stamp "probe $tag pairshape=$(python3 /tmp/glmflash/pairshape.py matches_ds14/probe_$tag.pgn cand | head -1) (recorded)"
  local ok=1 uci_line name value line n
  for uci_line in $cand_extra; do
    name=$(echo "$uci_line" | sed -n 's/option\.\([A-Za-z0-9]*\)=.*/\1/p')
    value=$(echo "$uci_line" | sed -n 's/.*=\(.*\)$/\1/p')
    line="setoption name $name value $value"
    n=$(grep -cF "$line" /tmp/glmflash/matches_ds14/probe_${tag}_uci_in.log 2>/dev/null || echo 0)
    stamp "probe $tag delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done
  for uci_line in $base_extra; do
    name=$(echo "$uci_line" | sed -n 's/option\.\([A-Za-z0-9]*\)=.*/\1/p')
    value=$(echo "$uci_line" | sed -n 's/.*=\(.*\)$/\1/p')
    line="setoption name $name value $value"
    n=$(grep -cF "$line" /tmp/glmflash/matches_ds14/probe_${tag}_uci_in.log 2>/dev/null || echo 0)
    stamp "probe $tag base-side delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done
  if [ "$ok" = "1" ]; then stamp "probe OK $tag"; return 0; else stamp "PROBEFAIL $tag"; return 1; fi
}

run_match() {
  local tag=$1 seed=$2 rounds=$3 limit=$4 cand_opts=$5 base_opts=$6
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds limit=${limit}s cand=($cand_opts) base=($base_opts)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.NodeClock=100 $cand_opts \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false option.NodeClock=100 $base_opts \
    -each proto=uci tc=10+0.1 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches_ds14/$tag.pgn min=true \
    > matches_ds14/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches_ds14/$tag.out > matches_ds14/${tag}_last40.txt
  stamp "warn $tag count=$(grep -c "doesn't have option" matches_ds14/$tag.out)"
  stamp "shape $tag $(python3 /tmp/glmflash/pairshape.py matches_ds14/$tag.pgn cand | head -1)"
}

if probe V1 8511 "option.TmSoftDivisor=16" ""; then run_match V1 7411 500 990 "option.TmSoftDivisor=16" ""; else stamp "skip V1 (probe failed)"; fi
if probe V2 8512 "option.TmSoftDivisor=30" ""; then run_match V2 7412 500 990 "option.TmSoftDivisor=30" ""; else stamp "skip V2 (probe failed)"; fi
# V3: the better of V1/V2 against 22 again; chosen from the two matches' own Elo lines
e1=$(grep -m1 -oE "Elo: -?[0-9]+\.[0-9]+" matches_ds14/V1.out | grep -oE "-?[0-9]+\.[0-9]+")
e2=$(grep -m1 -oE "Elo: -?[0-9]+\.[0-9]+" matches_ds14/V2.out | grep -oE "-?[0-9]+\.[0-9]+")
best=16
if [ -n "$e1" ] && [ -n "$e2" ]; then best=$(python3 -c "print(16 if float('$e1') >= float('$e2') else 30)"); fi
stamp "V3 divisor chosen: $best (V1 Elo ${e1:-unknown}, V2 Elo ${e2:-unknown})"
if probe V3 8513 "option.TmSoftDivisor=$best" ""; then run_match V3 7413 500 990 "option.TmSoftDivisor=$best" ""; else stamp "skip V3 (probe failed)"; fi
stamp "driver_ds14b done"
