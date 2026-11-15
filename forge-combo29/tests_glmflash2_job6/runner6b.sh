#!/bin/bash
# glmflash2 job 6, phase 2: S1..S4. Caps from control's measured rate
# (300 games in ~130 s => ~2.3 games/s => 2000 games ~ 870 s; cap 900 s).
# S4 is the first to be cut (absolute deadline 21:44:00Z), then S3.
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
ENG=/home/ubuntu/j6work_build/forge
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job6/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job6/pgn_stats.py

run_one() { # name seed games cap cand_spec base_spec
  local name=$1 seed=$2 games=$3 cap=$4 cand_spec=$5 base_spec=$6
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" $cand_spec $base_spec \
    -each proto=uci nodes=20000 \
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
  grep 'cand <--- setoption' /home/ubuntu/j5work/fc6/${name}_probe_engineio.log | grep -iv 'threads\|hash\|ownbook' > "$OUT/${name}_probe_setoption_lines.txt"
  grep '\[FEN' /home/ubuntu/j5work/fc6/${name}_probe.pgn | head -2 > "$OUT/${name}_probe_openings.txt"
  echo "PROBE $name candidate-lines=$(wc -l < "$OUT/${name}_probe_setoption_lines.txt")"
}

NONE_SPEC="-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false"
ASP2="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspFailHighReduce=1 option.AspFailHighMaxReduce=2"
ASP5="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspFailHighReduce=1 option.AspFailHighMaxReduce=5"
ASP1="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspFailHighReduce=1 option.AspFailHighMaxReduce=1"
ASP3BASE="-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false option.AspFailHighReduce=1 option.AspFailHighMaxReduce=3"

probe s1_mr2_vs_none 7261 "$ASP2" "$NONE_SPEC"
run_one s1_mr2_vs_none 7261 2000 900 "$ASP2" "$NONE_SPEC"
probe s2_mr5_vs_none 7262 "$ASP5" "$NONE_SPEC"
run_one s2_mr5_vs_none 7262 2000 900 "$ASP5" "$NONE_SPEC"
probe s3_mr5_vs_mr3 7263 "$ASP5" "$ASP3BASE"
run_one s3_mr5_vs_mr3 7263 2000 900 "$ASP5" "$ASP3BASE"
S4CAP=$(( $(date -u -d '2026-11-15T21:44:00Z' +%s) - $(date +%s) ))
if [ "$S4CAP" -gt 200 ]; then
  probe s4_mr1_vs_none 7264 "$ASP1" "$NONE_SPEC"
  run_one s4_mr1_vs_none 7264 2000 "$S4CAP" "$ASP1" "$NONE_SPEC"
else
  echo "S4_SKIPPED only ${S4CAP}s left $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
fi
echo "PHASE2_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
