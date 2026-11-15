#!/bin/bash
# glmflash2 job 4 runner B: second seeds in the order of the first results
# (largest first): c3 TtProbcut (7253), c1 PruneLmrHist (7251), c2 QsMovePrune
# (7252). Same probe-then-match pattern as runner4a.
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
J=/home/ubuntu/j4work
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job4/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job4/pgn_stats.py

run_one() {
  local name=$1 seed=$2 games=$3 cap=$4 cexe=$5 cextra=$6
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$cexe" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cextra \
    -engine cmd="$cexe" name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=$J/fc4/$name.pgn min=true \
    -log file=$J/fc4/${name}_engineio.log level=trace engine=true append=false \
    > $J/fc4/${name}_out.txt 2>&1 &
  local FCPID=$!
  local DEAD=$(( $(date +%s) + cap ))
  while kill -0 $FCPID 2>/dev/null && [ "$(date +%s)" -lt "$DEAD" ]; do sleep 10; done
  if kill -0 $FCPID 2>/dev/null; then
    kill -INT $FCPID
    for i in $(seq 1 12); do kill -0 $FCPID 2>/dev/null || break; sleep 5; done
    kill -9 $FCPID 2>/dev/null
  fi
  wait $FCPID 2>/dev/null
  echo "END $name $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 $J/fc4/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" $J/fc4/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

probe() {
  local name=$1 seed=$2 cexe=$3 cextra=$4
  "$FC" \
    -engine cmd="$cexe" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cextra \
    -engine cmd="$cexe" name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds 1 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=$J/fc4/${name}_probe.pgn min=true \
    -log file=$J/fc4/${name}_probe_engineio.log level=trace engine=true append=false \
    > $J/fc4/${name}_probe_out.txt 2>&1
  grep "setoption name" $J/fc4/${name}_probe_engineio.log | grep -iv 'threads\|hash\|ownbook\|proto\|uci' | head -4 > "$OUT/${name}_probe_setoption_lines.txt"
  grep '\[FEN' $J/fc4/${name}_probe.pgn | head -2 > "$OUT/${name}_probe_openings.txt"
  echo "PROBE $name: $(head -1 "$OUT/${name}_probe_setoption_lines.txt")"
}

probe m4_ttprobcut_s2 7253 "$J/build_c3_ttprobcut/forge" "option.TtProbcut=360"
run_one m4_ttprobcut_s2 7253 2000 700 "$J/build_c3_ttprobcut/forge" "option.TtProbcut=360"
probe m5_prunelmrhist_s2 7251 "$J/build_c1/forge" "option.PruneLmrHist=1"
run_one m5_prunelmrhist_s2 7251 2000 700 "$J/build_c1/forge" "option.PruneLmrHist=1"
M6CAP=$(( $(date -u -d '2026-11-15T19:05:00Z' +%s) - $(date +%s) ))
probe m6_qsmoveprune_s2 7252 "$J/build_c2_qsmoveprune/forge" "option.QsMovePrune=3"
run_one m6_qsmoveprune_s2 7252 2000 "$M6CAP" "$J/build_c2_qsmoveprune/forge" "option.QsMovePrune=3"
echo "RUNNER4B_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
