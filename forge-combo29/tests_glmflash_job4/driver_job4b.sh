#!/bin/bash
# glmflash job4 driver B (corrected gate): probe = option delivery + bench pin only
# (a single 2-game pair cannot prove non-degeneracy); the pair-shape check runs on the MATCH.
cd /tmp/glmflash
EXE=/tmp/forge_packc28/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+42 minutes' +%s)

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

# probe with a generated tee+inject wrapper; args: tag inject_lines_file expect_b13 seed
probe() {
  local tag=$1 inject=$2 expect=$3 seed=$4
  local wp=/tmp/glmflash/matches4/wp_$tag.sh
  {
    echo '#!/bin/sh'
    echo "{ printf '$inject'; cat; } | tee -a /tmp/glmflash/matches4/probe_${tag}_uci_in.log | $EXE"
  } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches4/probe_$tag.pgn min=true \
    > matches4/probe_$tag.out 2>&1
  local shape=$(python3 /tmp/glmflash/pairshape.py matches4/probe_$tag.pgn cand | head -1)
  stamp "probe $tag pairshape=$shape (recorded, not a gate at 2 games)"
  local ok=1
  # check every option line of the inject block arrives at least once per game
  while IFS= read -r line; do
    local name=$(echo "$line" | sed -n 's/setoption name \([A-Za-z0-9]*\) value.*/\1/p')
    local n=$(grep -c "^$line\$" /tmp/glmflash/matches4/probe_${tag}_uci_in.log)
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
    -ratinginterval 100 -pgnout file=matches4/$tag.pgn min=true \
    > matches4/$tag.out 2>&1
  stamp "end $tag exit=$?"
  tail -40 matches4/$tag.out > matches4/${tag}_last40.txt
  stamp "warn $tag count=$(grep -c "doesn't have option" matches4/$tag.out)"
  stamp "shape $tag $(python3 /tmp/glmflash/pairshape.py matches4/$tag.pgn cand | head -1)"
}

mkdir -p matches4
INJ4=/tmp/glmflash/inj4.txt
INJSWING=/tmp/glmflash/injswing.txt
INJASP=/tmp/glmflash/injasp.txt
printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\nsetoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n' > "$INJ4"
printf 'setoption name EvalSwingMult value 24\nsetoption name EvalSwingMax value 200\n' > "$INJSWING"
printf 'setoption name AspFailHighReduce value 1\nsetoption name AspFailHighMaxReduce value 3\n' > "$INJASP"

# C: probe (no options; only Threads/Hash/OwnBook delivery is expected from fastchess)
probe C /dev/null "-" 8040
stamp "start C seed=7140"
timeout -s INT --kill-after=20 $(( STOP - $(date +%s) )) $FC \
  -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
  -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
  -each proto=uci \
  -openings file=$BOOK format=epd order=random \
  -srand 7140 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
  -ratinginterval 100 -pgnout file=matches4/C.pgn min=true \
  > matches4/C.out 2>&1
stamp "end C exit=$?"
tail -40 matches4/C.out > matches4/C_last40.txt
stamp "warn C count=$(grep -c "doesn't have option" matches4/C.out)"
stamp "shape C $(python3 /tmp/glmflash/pairshape.py matches4/C.pgn cand | head -1)"

# M1
if probe M1 "$INJ4" 690187 8041; then run_match M1 7141 1000 /tmp/glmflash/w4_c28.sh $EXE 960; else stamp "skip M1 (probe failed)"; fi
# M2
if probe M2 "$INJSWING" "-" 8042; then run_match M2 7142 1000 /tmp/glmflash/wswing_c28.sh $EXE 870; else stamp "skip M2 (probe failed)"; fi
# M3
if probe M3 "$INJASP" "-" 8043; then run_match M3 7143 1000 /tmp/glmflash/wasp_c28.sh $EXE 990; else stamp "skip M3 (probe failed)"; fi
stamp "driver4b done"
