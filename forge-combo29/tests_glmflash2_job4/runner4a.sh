#!/bin/bash
# glmflash2 job 4 runner. Before every match: a 2-game probe with the match's
# exact command (same seed, same flags) plus the engine input log, so the
# setoption lines the cand side received are on file; the probe's openings are
# the match's first pair (same seed). Then the real match, also with its engine
# input log on. C first, then M1-M3; M4-M6 are the second seeds (the report
# maps them to candidates by the first-seed ranking).
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
J=/home/ubuntu/j4work
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job4/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job4/pgn_stats.py

run_one() { # name seed games cap cexe cextra cnodes bnodes
  local name=$1 seed=$2 games=$3 cap=$4 cexe=$5 cextra=$6 cnodes=$7 bnodes=$8
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$cexe" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cextra \
    -engine cmd="$cexe" name=base option.Threads=1 option.Hash=16 option.OwnBook=false \
    -each proto=uci \
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

probe() { # name seed cexe cextra
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
  echo "PROBE $name: $(cat "$OUT/${name}_probe_setoption_lines.txt" | tr '\n' ';')"
}

mkdir -p $J/fc4 "$OUT"
probe control_7240 7240 "$J/build_c1/forge" ""
run_one control_7240 7240 300 300 "$J/build_c1/forge" "" "nodes=20000" "nodes=10000"
probe m1_prunelmrhist 7241 "$J/build_c1/forge" "option.PruneLmrHist=1"
run_one m1_prunelmrhist 7241 2000 700 "$J/build_c1/forge" "option.PruneLmrHist=1" "nodes=20000" "nodes=20000"
probe m2_qsmoveprune 7242 "$J/build_c2_qsmoveprune/forge" "option.QsMovePrune=3"
run_one m2_qsmoveprune 7242 2000 700 "$J/build_c2_qsmoveprune/forge" "option.QsMovePrune=3" "nodes=20000" "nodes=20000"
probe m3_ttprobcut 7243 "$J/build_c3_ttprobcut/forge" "option.TtProbcut=360"
run_one m3_ttprobcut 7243 2000 700 "$J/build_c3_ttprobcut/forge" "option.TtProbcut=360" "nodes=20000" "nodes=20000"
echo "RUNNER4A_DONE $(date -u +%FT%TZ)" >> "/agent/repos/dwqww/forge-combo29/tests_glmflash2_job4/matches/timeline.txt"
