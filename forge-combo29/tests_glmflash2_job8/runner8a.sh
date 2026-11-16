#!/bin/bash
# glmflash2 job 8 runner. Probe before every match. C first; its wall time sets
# the caps (games/rate, fifth of reserve). Y4 deadline 00:39:00Z, cut first.
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
ENG=/home/ubuntu/j8work/build_base/forge
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job8/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job8/pgn_stats.py

run_one() { # name seed games cap cand_spec base_spec
  local name=$1 seed=$2 games=$3 cap=$4 cand_spec=$5 base_spec=$6
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" $cand_spec $base_spec \
    -each proto=uci \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/home/ubuntu/j5work/fc8/$name.pgn min=true \
    -log file=/home/ubuntu/j5work/fc8/${name}_engineio.log level=trace engine=true append=false \
    > /home/ubuntu/j5work/fc8/${name}_out.txt 2>&1 &
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
  tail -n 40 /home/ubuntu/j5work/fc8/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /home/ubuntu/j5work/fc8/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  grep 'Finished game' /home/ubuntu/j5work/fc8/${name}_out.txt > "$OUT/${name}_endings.txt"
  awk -F'[{}]' '{print $2}' "$OUT/${name}_endings.txt" | sort | uniq -c | sort -rn > "$OUT/${name}_ending_tally.txt"
  head -n 3 "$OUT/${name}_lines.txt"
}

probe() { # name seed cand_spec base_spec
  local name=$1 seed=$2 cand_spec=$3 base_spec=$4
  "$FC" $cand_spec $base_spec \
    -each proto=uci \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds 1 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/home/ubuntu/j5work/fc8/${name}_probe.pgn min=true \
    -log file=/home/ubuntu/j5work/fc8/${name}_probe_engineio.log level=trace engine=true append=false \
    > /home/ubuntu/j5work/fc8/${name}_probe_out.txt 2>&1
  grep 'cand <--- setoption' /home/ubuntu/j5work/fc8/${name}_probe_engineio.log | grep -iv 'threads\|hash\|ownbook' > "$OUT/${name}_probe_setoption_lines.txt"
  grep '\[FEN' /home/ubuntu/j5work/fc8/${name}_probe.pgn | head -2 > "$OUT/${name}_probe_openings.txt"
  echo "PROBE $name candidate-lines=$(wc -l < "$OUT/${name}_probe_setoption_lines.txt")"
}

mkdir -p /home/ubuntu/j5work/fc8 "$OUT"
CTRL_C="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000"
CTRL_B="-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000"
ARM="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspArmLate=true nodes=20000"
CAP="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=true nodes=20000"
BOTH="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspArmLate=true option.AspCappedReopen=true nodes=20000"
NONE="-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000"

probe control_8310 8310 "$CTRL_C" "$CTRL_B"
T0=$(date +%s)
run_one control_8310 8310 300 300 "$CTRL_C" "$CTRL_B"
T1=$(date +%s)
D=$((T1 - T0)); [ "$D" -lt 30 ] && D=30
RATE20=$(python3 -c "print(round(300/$D, 3))")
CAP2000=$(python3 -c "print(int(2000/$RATE20*1.2)+60)")
echo "RATE20=$RATE20 CAP2000=$CAP2000" >> "$OUT/timeline.txt"
probe y1_armlate 8311 "$ARM" "$NONE"
run_one y1_armlate 8311 2000 "$CAP2000" "$ARM" "$NONE"
probe y2_capped 8312 "$CAP" "$NONE"
run_one y2_capped 8312 2000 "$CAP2000" "$CAP" "$NONE"
echo "RUNNER8A_DONE $(date -u +%FT%TZ)" >> "/agent/repos/dwqww/forge-combo29/tests_glmflash2_job8/matches/timeline.txt"
