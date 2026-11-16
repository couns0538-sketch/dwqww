#!/bin/bash
# glmflash2 job 8, phase B: Y3 (both on vs both off), then Y4 = the better
# single switch (AspCappedReopen: Y1 -20.0 +/- 10.7 vs Y2 -8.7 +/- 11.3)
# with its second seed 8314. Y4 deadline 00:39:00Z (cut first, then Y3).
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

BOTH="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspArmLate=true option.AspCappedReopen=true nodes=20000"
NONE="-engine cmd=$ENG name=base option.Threads=1 option.Hash=16 option.OwnBook=false nodes=20000"
CAPPED="-engine cmd=$ENG name=cand option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=true nodes=20000"

probe y3_both 8313 "$BOTH" "$NONE"
run_one y3_both 8313 2000 859 "$BOTH" "$NONE"
Y4CAP=$(( $(date -u -d '2026-11-16T00:39:00Z' +%s) - $(date +%s) ))
echo "Y4CAP=$Y4CAP $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
if [ "$Y4CAP" -gt 400 ]; then
  probe y4_capped_s2 8314 "$CAPPED" "$NONE"
  run_one y4_capped_s2 8314 2000 "$Y4CAP" "$CAPPED" "$NONE"
else
  echo "Y4_SKIPPED only ${Y4CAP}s left $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
fi
echo "RUNNER8B_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
