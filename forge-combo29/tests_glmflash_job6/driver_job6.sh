#!/bin/bash
# glmflash job6 driver: probe (2 games, exact match command, tee'd cand input) before every match.
# Matches: cm exe both sides; cand carries option.CorrMargin=K, base none.
cd /tmp/glmflash
EXE=/tmp/forge_cm/build/forge
BOOK=/tmp/glmflash/UHO_Lichess_4852_v1.epd
FC=/tmp/glmflash/fastchess/fastchess
STOP=$(date -d '+56 minutes' +%s)
mkdir -p matches6

stamp() { echo "$(date -u +%FT%TZ) $1" >> /tmp/glmflash/stamps.txt; }

probe() {
  local tag=$1 seed=$2 cand_extra=$3 base_extra=$4
  local wp=/tmp/glmflash/matches6/wp_$tag.sh
  { echo '#!/bin/sh'; echo "exec tee -a /tmp/glmflash/matches6/probe_${tag}_uci_in.log | exec $EXE"; } > "$wp"
  chmod +x "$wp"
  stamp "probe start $tag"
  timeout -s INT --kill-after=20 300 $FC \
    -engine cmd=$wp name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_extra nodes=20000 \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false $base_extra nodes=10000 \
    -each proto=uci \
    -openings file=$BOOK format=epd order=random \
    -srand $seed -rounds 1 -games 2 -repeat -concurrency 2 -recover \
    -ratinginterval 100 -pgnout file=matches6/probe_$tag.pgn min=true \
    > matches6/probe_$tag.out 2>&1
  local shape=$(python3 /tmp/glmflash/pairshape.py matches6/probe_$tag.pgn cand | head -1)
  stamp "probe $tag pairshape=$shape"
  local ok=1
  if [ "$cand_extra" != "-" ]; then
    local n=$(grep -cF "$cand_extra" /tmp/glmflash/matches6/probe_${tag}_uci_in.log)
    stamp "probe $tag delivered: $cand_extra x$n"
    [ "$n" -ge 2 ] || ok=0
  fi
  if [ "$shape" = "DEGENERATE" ] && [ "$cand_extra" != "-" ]; then stamp "PROBEFAIL $tag degenerate despite option"; ok=0; fi
  if [ "$ok" = "1" ]; then stamp "probe OK $tag"; return 0; else stamp "PROBEFAIL $tag"; return 1; fi
}

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

# C: control 20000 vs 10000, no options, 300 games, seed 7160
if probe C 8060 "-" "-"; then
  stamp "start C seed=7160"
  timeout -s INT --kill-after=20 $(( STOP - $(date +%s) )) $FC \
    -engine cmd=$EXE name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000 \
    -engine cmd=$EXE name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000 \
    -each proto=uci \
    -openings file=$BOOK format=epd order=random \
    -srand 7160 -rounds 150 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=matches6/C.pgn min=true \
    > matches6/C.out 2>&1
  stamp "end C exit=$?"
  tail -40 matches6/C.out > matches6/C_last40.txt
  stamp "warn C count=$(grep -c "doesn't have option" matches6/C.out)"
  stamp "shape C $(python3 /tmp/glmflash/pairshape.py matches6/C.pgn cand | head -1)"
else stamp "skip C (probe failed)"; fi

# M1: CorrMargin=24 (mild) on vs off, 2000 games, seed 7161
if probe M1 8061 "option.CorrMargin=24" "-"; then run_match M1 7161 1000 975 option.CorrMargin=24; else stamp "skip M1 (probe failed)"; fi
# M3: CorrMargin=64 (strong) on vs off, 2000 games, seed 7163
if probe M3 8063 "option.CorrMargin=64" "-"; then run_match M3 7163 1000 975 option.CorrMargin=64; else stamp "skip M3 (probe failed)"; fi
# M2: CorrMargin=24 second seed, 2000 games, seed 7162 (cut if the clock ends it)
if probe M2 8062 "option.CorrMargin=24" "-"; then run_match M2 7162 1000 975 option.CorrMargin=24; else stamp "skip M2 (probe failed)"; fi
# M4: CorrMargin=64 second seed, 2000 games, seed 7164
if probe M4 8064 "option.CorrMargin=64" "-"; then run_match M4 7164 1000 975 option.CorrMargin=64; else stamp "skip M4 (probe failed)"; fi
stamp "driver6 done"
