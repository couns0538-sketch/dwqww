#!/bin/bash
# glmflash2 job 6, phase 1: probe + control only (rate measurement).
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
ENG=/home/ubuntu/j6work_build/forge
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job6/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job6/pgn_stats.py

run_one() { # name seed games cap cand_spec base_spec
  local name=$1 seed=$2 games=$3 cap=$4 cand_spec=$5 base_spec=$6
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" $cand_spec $base_spec \
    -each proto=uci \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/home/ubuntu/j5work/fc6/$name.pgn min=true \
    -log file=/home/ubuntu/j5work/fc6/${name}_engineio.log level=trace engine=true append=false \
    > /home/ubuntu/j5work/fc6/${name}_out.txt 2>&1 &
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
  tail -n 40 /home/ubuntu/j5work/fc6/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /home/ubuntu/j5work/fc6/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

probe() { # name seed cand_spec base_spec
  local name=$1 seed=$2 cand_spec=$3 base_spec=$4
  "$FC" $cand_spec $base_spec \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds 1 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/home/ubuntu/j5work/fc6/${name}_probe.pgn min=true \
    -log file=/home/ubuntu/j5work/fc6/${name}_probe_engineio.log level=trace engine=true append=false \
    > /home/ubuntu/j5work/fc6/${name}_probe_out.txt 2>&1
  grep 'cand <--- setoption' /home/ubuntu/j5work/fc6/${name}_probe_engineio.log > "$OUT/${name}_probe_setoption_lines.txt"
  grep '\[FEN' /home/ubuntu/j5work/fc6/${name}_probe.pgn | head -2 > "$OUT/${name}_probe_openings.txt"
  echo "PROBE $name setoption-lines=$(wc -l < "$OUT/${name}_probe_setoption_lines.txt")"
}

mkdir -p /home/ubuntu/j5work/fc6 "$OUT"
probe control_7260 7260 \
  "-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000" \
  "-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000"
run_one control_7260 7260 300 300 \
  "-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000" \
  "-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=10000"
echo "PHASE1_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
