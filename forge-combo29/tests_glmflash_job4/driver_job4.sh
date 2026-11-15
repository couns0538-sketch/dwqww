#!/bin/bash
# glmflash job4 driver: probe (2 games, input log) before EVERY match, then the match.
cd /tmp/glmflash
EXE=/tmp/forge_packc28/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
mkdir -p matches4
STOP=$(date -d '+73 minutes' +%s)

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

# probe: exact match command shape, 2 games, its own seed, tee-wrapper on cand.
# args: tag probe_wrapper expect_b13(optional "-" = none) seed match_args...
probe() {
  local tag=$1 pwrap=$2 expect=$3 seed=$4; shift 4
  rm -f /tmp/glmflash/probe_${tag}_uci_in.log
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$pwrap name=cand option.Threads=1 option.Hash=16 option.OwnBook=false \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches4/probe_$tag.pgn min=true \
    > matches4/probe_$tag.out 2>&1
  local opts_received=$(grep -c "^setoption name" /tmp/glmflash/probe_${tag}_uci_in.log)
  local shape
  shape=$(python3 /tmp/glmflash/pairshape.py matches4/probe_$tag.pgn cand)
  local b13="-"
  if [ "$expect" != "-" ]; then
    b13=$(printf 'uci\nbench 13\nquit\n' | timeout 120 "$pwrap" 2>&1 | grep -oE "bench depth 13 nodes [0-9]+" | grep -oE "[0-9]+$")
  fi
  stamp "probe end $tag setoption_lines=$opts_received pairshape=$shape bench13=$b13 (expect $expect)"
  if [ "$expect" != "-" ] && [ "$b13" != "$expect" ]; then stamp "PROBEFAIL $tag bench13"; return 1; fi
  if [ "$opts_received" -lt 2 ]; then stamp "PROBEFAIL $tag options"; return 1; fi
  if [ "$shape" = "DEGENERATE" ]; then stamp "PROBEFAIL $tag degenerate"; return 1; fi
  stamp "probe OK $tag"
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
  local w=$(grep -c "doesn't have option" matches4/$tag.out)
  stamp "warn $tag count=$w"
}

# C: 20,000 vs 10,000 nodes, no options, 300 games, seed 7140 (per-engine nodes, probe with no bench pin)
if probe C /tmp/glmflash/plain_tee_c28.sh "-" 8040; then
  stamp "start C seed=8040(per-probe) match-seed=7140"
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
else
  stamp "skip C (probe failed)"
fi
# M1: four gate options vs none, 2000 games, seed 7141
if probe M1 /tmp/glmflash/wp4_c28.sh 690187 8041; then
  run_match M1 7141 1000 /tmp/glmflash/w4_c28.sh $EXE 990
else stamp "skip M1 (probe failed)"; fi
# M2: EvalSwing pair alone, 2000 games, seed 7142
if probe M2 /tmp/glmflash/wpswing_c28.sh "-" 8042; then
  run_match M2 7142 1000 /tmp/glmflash/wswing_c28.sh $EXE 990
else stamp "skip M2 (probe failed)"; fi
# M3: Asp pair alone, 2000 games, seed 7143
if probe M3 /tmp/glmflash/wpasp_c28.sh "-" 8043; then
  run_match M3 7143 1000 /tmp/glmflash/wasp_c28.sh $EXE 990
else stamp "skip M3 (probe failed)"; fi
# M4: five options (cand wrapper) vs four options (base wrapper), 2000 games, seed 7144
if probe M4 /tmp/glmflash/wp5_c28.sh "-" 8044; then
  run_match M4 7144 1000 /tmp/glmflash/w5_c28.sh /tmp/glmflash/w4_c28.sh 990
else stamp "skip M4 (probe failed)"; fi
# M5: EvalSwingMult 48 + EvalSwingMax 200 alone, 1500 games, seed 7145 — only if time
if probe M5 /tmp/glmflash/wpswing48_c28.sh "-" 8045; then
  run_match M5 7145 750 /tmp/glmflash/wswing48_c28.sh $EXE 990
else stamp "skip M5 (probe failed or no time)"; fi
stamp "driver4 done"
