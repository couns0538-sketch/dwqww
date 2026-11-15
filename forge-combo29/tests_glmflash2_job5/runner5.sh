#!/bin/bash
# glmflash2 job 5 runner. Probe (2 games, match's exact command, engine log)
# before every match. C first; M1 (5k), M2 (80k, cap 1750 - must complete),
# M3 (80k, absolute deadline cut, not M2), M4 (5k, only with leftover time).
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
J=/home/ubuntu/j5work
ENG=$J/build_packc28/forge
WRAP=$J/wrapper_packc28.sh
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job5/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job5/pgn_stats.py

run_one() { # name seed games cap candcmd cnodes bnodes
  local name=$1 seed=$2 games=$3 cap=$4 candcmd=$5 cnodes=$6 bnodes=$7
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$candcmd" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cnodes \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $bnodes \
    -each proto=uci \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=$J/fc5/$name.pgn min=true \
    -log file=$J/fc5/${name}_engineio.log level=trace engine=true append=false \
    > $J/fc5/${name}_out.txt 2>&1 &
  local FCPID=$!
  local DEAD=$(( $(date +%s) + cap ))
  while kill -0 $FCPID 2>/dev/null && [ "$(date +%s)" -lt "$DEAD" ]; do sleep 10; done
  if kill -0 $FCPID 2>/dev/null; then
    kill -INT $FCPID
    for i in $(seq 1 15); do kill -0 $FCPID 2>/dev/null || break; sleep 5; done
    kill -9 $FCPID 2>/dev/null
  fi
  wait $FCPID 2>/dev/null
  echo "END $name $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 $J/fc5/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" $J/fc5/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

probe() { # name seed candcmd
  local name=$1 seed=$2 candcmd=$3
  "$FC" \
    -engine cmd="$candcmd" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds 1 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=$J/fc5/${name}_probe.pgn min=true \
    -log file=$J/fc5/${name}_probe_engineio.log level=trace engine=true append=false \
    > $J/fc5/${name}_probe_out.txt 2>&1
  grep -c 'AspFailHighReduce\|EvalSwingMult' $J/fc5/${name}_probe_engineio.log > "$OUT/${name}_probe_wrapper_lines.txt"
  grep '\[FEN' $J/fc5/${name}_probe.pgn | head -2 > "$OUT/${name}_probe_openings.txt"
  echo "PROBE $name wrapper-lines=$(cat "$OUT/${name}_probe_wrapper_lines.txt")"
}

mkdir -p $J/fc5 "$OUT"
probe control_7250 7250 "$ENG"
run_one control_7250 7250 300 300 "$ENG" "nodes=20000" "nodes=10000"
probe m1_5k_7251 7251 "$WRAP"
run_one m1_5k_7251 7251 3000 700 "$WRAP" "nodes=5000" "nodes=5000"
probe m2_80k_7252 7252 "$WRAP"
run_one m2_80k_7252 7252 1000 1750 "$WRAP" "nodes=80000" "nodes=80000"
M3CAP=$(( $(date -u -d '2026-11-15T20:22:00Z' +%s) - $(date +%s) ))
probe m3_80k_7253 7253 "$WRAP"
run_one m3_80k_7253 7253 1000 "$M3CAP" "$WRAP" "nodes=80000" "nodes=80000"
M4LEFT=$(( $(date -u -d '2026-11-15T20:27:00Z' +%s) - $(date +%s) ))
if [ "$M4LEFT" -gt 330 ]; then
  probe m4_5k_7254 7254 "$WRAP"
  run_one m4_5k_7254 7254 3000 "$M4LEFT" "$WRAP" "nodes=5000" "nodes=5000"
else
  echo "M4_SKIPPED only ${M4LEFT}s left $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
fi
echo "RUNNER5_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
