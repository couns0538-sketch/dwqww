#!/bin/bash
# deepseek job13 driver (executed by glmflash): probe before every match; C then M1,M2,M3,M4.
cd /tmp/glmflash
EXE=/tmp/ds13_o1/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
mkdir -p matches_ds13

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

probe() {
  local tag=$1 seed=$2 cand_extra=$3 base_extra=$4
  local wp=/tmp/glmflash/matches_ds13/wp_$tag.sh
  { echo '#!/bin/sh'; echo "exec tee -a /tmp/glmflash/matches_ds13/probe_${tag}_uci_in.log | exec $EXE"; } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_extra nodes=20000 \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $base_extra nodes=10000 \
    -each proto=uci \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches_ds13/probe_$tag.pgn min=true \
    > matches_ds13/probe_$tag.out 2>&1
  stamp "probe $tag pairshape=$(python3 /tmp/glmflash/pairshape.py matches_ds13/probe_$tag.pgn cand | head -1) (recorded)"
  local ok=1 line uci_line n
  for uci_line in $cand_extra; do
    [ "$uci_line" = "-" ] && continue
    local name=$(echo "$uci_line" | sed -n 's/option\.\([A-Za-z0-9]*\)=.*/\1/p')
    local value=$(echo "$uci_line" | sed -n 's/.*=\(.*\)$/\1/p')
    line="setoption name $name value $value"
    n=$(grep -cF "$line" /tmp/glmflash/matches_ds13/probe_${tag}_uci_in.log 2>/dev/null || echo 0)
    stamp "probe $tag delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done
  for uci_line in $base_extra; do
    [ "$uci_line" = "-" ] && continue
    local name=$(echo "$uci_line" | sed -n 's/option\.\([A-Za-z0-9]*\)=.*/\1/p')
    local value=$(echo "$uci_line" | sed -n 's/.*=\(.*\)$/\1/p')
    line="setoption name $name value $value"
    n=$(grep -cF "$line" /tmp/glmflash/matches_ds13/probe_${tag}_uci_in.log 2>/dev/null || echo 0)
    stamp "probe $tag base-side delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done
  if [ "$ok" = "1" ]; then stamp "probe OK $tag"; return 0; else stamp "PROBEFAIL $tag (delivery only; 1-pair shape is recorded, not a gate)"; return 1; fi
}

run_match() {
  local tag=$1 seed=$2 rounds=$3 limit=$4 cand_opts=$5 base_opts=$6
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds limit=${limit}s cand=($cand_opts) base=($base_opts)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_opts \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $base_opts \
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

STOP=$(date -d '+58 minutes' +%s)

# C: control, per-engine nodes, no options
if probe C 8500 "-" "-"; then
  stamp "start C seed=7400"
  timeout -s INT --kill-after=20 210 $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
    -each proto=uci \
    -openings file=$BOOK format=epd order=random \
    -srand 7400 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches_ds13/C.pgn min=true \
    > matches_ds13/C.out 2>&1
  stamp "end C exit=$?"
  tail -40 matches_ds13/C.out > matches_ds13/C_last40.txt
  stamp "warn C count=$(grep -c "doesn't have option" matches_ds13/C.out)"
  stamp "shape C $(python3 /tmp/glmflash/pairshape.py matches_ds13/C.pgn cand | head -1)"
  stamp "C rate note: see C_total_time in C_last40.txt; later limits set from it"
else stamp "skip C (probe failed)"; fi

# M1: both on vs none
if probe M1 8501 "option.PawnHistory=true option.ContHistDeep=1" "-"; then run_match M1 7401 1000 975 "option.PawnHistory=true option.ContHistDeep=1" ""; else stamp "skip M1 (probe failed)"; fi
# M2: both on vs PawnHistory only
if probe M2 8502 "option.PawnHistory=true option.ContHistDeep=1" "option.PawnHistory=true"; then run_match M2 7402 1000 975 "option.PawnHistory=true option.ContHistDeep=1" "option.PawnHistory=true"; else stamp "skip M2 (probe failed)"; fi
# M3: both on vs none, second seed
if probe M3 8503 "option.PawnHistory=true option.ContHistDeep=1" "-"; then run_match M3 7403 1000 975 "option.PawnHistory=true option.ContHistDeep=1" ""; else stamp "skip M3 (probe failed)"; fi
# M4: both on vs ContHistDeep 1 only
if probe M4 8504 "option.PawnHistory=true option.ContHistDeep=1" "option.ContHistDeep=1"; then run_match M4 7404 1000 975 "option.PawnHistory=true option.ContHistDeep=1" "option.ContHistDeep=1"; else stamp "skip M4 (probe failed)"; fi
stamp "driver_ds13 done"
