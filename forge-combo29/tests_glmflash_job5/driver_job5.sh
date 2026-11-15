#!/bin/bash
# glmflash job5 driver: Step 0 failed (patch conflict, both orders) -> Part B only.
# C (control), B1m (Asp pair alone), B2m (EvalSwing pair alone). Probe before every match.
cd /tmp/glmflash
EXE=/tmp/forge_packc28/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+70 minutes' +%s)
mkdir -p matches5

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

probe() {
  local tag=$1 inject=$2 expect=$3 seed=$4
  local wp=/tmp/glmflash/matches5/wp_$tag.sh
  {
    echo '#!/bin/sh'
    echo "{ cat $inject; cat; } | tee -a /tmp/glmflash/matches5/probe_${tag}_uci_in.log | $EXE"
  } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches5/probe_$tag.pgn min=true \
    > matches5/probe_$tag.out 2>&1
  stamp "probe $tag pairshape=$(python3 /tmp/glmflash/pairshape.py matches5/probe_$tag.pgn cand | head -1) (recorded, not a gate at 2 games)"
  local ok=1 line n
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    n=$(grep -cF "$line" /tmp/glmflash/matches5/probe_${tag}_uci_in.log)
    stamp "probe $tag delivered: $line x$n"
    [ "$n" -ge 2 ] || ok=0
  done < "$inject"
  if [ "$expect" != "-" ]; then
    local b13=$(printf 'uci\nbench 13\nquit\n' | timeout 120 "$wp" 2>&1 | grep -oE "bench depth 13 nodes [0-9]+" | grep -oE "[0-9]+$")
    stamp "probe $tag bench13=$b13 (expect $expect)"
    [ "$b13" = "$expect" ] || ok=0
  fi
  if [ "$ok" = "1" ]; then stamp "probe OK $tag"; return 0; else stamp "PROBEFAIL $tag"; return 1; fi
}

run_match() {
  local tag=$1 seed=$2 rounds=$3 cand_cmd=$4 base_cmd=$5 limit=$6; shift 6
  local remaining=$(( STOP - $(date +%s) ))
  if [ "$limit" -gt "$remaining" ]; then limit=$remaining; fi
  if [ "$remaining" -lt 120 ]; then stamp "skip $tag (remaining ${remaining}s < 120s)"; return; fi
  stamp "start $tag seed=$seed rounds=$rounds cand_cmd=$cand_cmd base_cmd=$base_cmd limit=${limit}s args=($*)"
  timeout -s INT --kill-after=20 "$limit" $FC \
    -engine cmd=$cand_cmd name=cand option.Threads=1 option.Hash=16 option.OwnBook=false "$@" \
    -engine cmd=$base_cmd name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds $rounds -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches5/$tag.pgn min=true \
    > matches5/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches5/$tag.out > matches5/${tag}_last40.txt
  stamp "warn $tag count=$(grep -c "doesn't have option" matches5/$tag.out)"
  stamp "shape $tag $(python3 /tmp/glmflash/pairshape.py matches5/$tag.pgn cand | head -1)"
}

# C: control, 20000 vs 10000, no options, 300 games, seed 7150; probe expects no inject, bench "-"
probe C /dev/null "-" 8050
stamp "start C seed=7150"
timeout -s INT --kill-after=20 210 $FC \
  -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci \
  -openings file=$BOOK format=epd order=random \
  -srand 7150 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=matches5/C.pgn min=true \
  > matches5/C.out 2>&1
stamp "end C exit=$?"
tail -40 matches5/C.out > matches5/C_last40.txt
stamp "warn C count=$(grep -c "doesn't have option" matches5/C.out)"
stamp "shape C $(python3 /tmp/glmflash/pairshape.py matches5/C.pgn cand | head -1)"

# B1m: Asp pair alone, 2000 games, seed 7153
if probe B1m /tmp/glmflash/injasp.txt "-" 8053; then run_match B1m 7153 1000 /tmp/glmflash/wasp_c28.sh $EXE 975; else stamp "skip B1m (probe failed)"; fi
# B2m: EvalSwing pair alone, 2000 games, seed 7154
if probe B2m /tmp/glmflash/injswing.txt "-" 8054; then run_match B2m 7154 1000 /tmp/glmflash/wswing_c28.sh $EXE 975; else stamp "skip B2m (probe failed)"; fi
stamp "driver5 done"
