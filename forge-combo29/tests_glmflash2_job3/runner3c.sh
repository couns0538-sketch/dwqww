#!/bin/bash
# glmflash2 job 3 runner, clean relaunch: M1..M6 only (control 7230 already done).
FC=/home/ubuntu/j3work/fastchess/fastchess
BOOK=/home/ubuntu/j3work/UHO_Lichess_4852_v1.epd
B=/home/ubuntu/j3work/j3build
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job3/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job3/pgn_stats.py

run_match() {
  name=$1; cand_engine=$2; cand_opts=$3; base_engine=$4; base_opts=$5; seed=$6; games=$7; cap=$8
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$cand_engine" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_opts \
    -engine cmd="$base_engine" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $base_opts \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/home/ubuntu/j3work/fc3/$name.pgn min=true \
    > /home/ubuntu/j3work/fc3/${name}_out.txt 2>&1 &
  FCPID=$!
  DEAD=$(( $(date +%s) + cap ))
  while kill -0 $FCPID 2>/dev/null && [ "$(date +%s)" -lt "$DEAD" ]; do sleep 10; done
  if kill -0 $FCPID 2>/dev/null; then
    kill -INT $FCPID
    for i in $(seq 1 12); do kill -0 $FCPID 2>/dev/null || break; sleep 5; done
    kill -9 $FCPID 2>/dev/null
  fi
  wait $FCPID 2>/dev/null
  echo "END $name $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 /home/ubuntu/j3work/fc3/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /home/ubuntu/j3work/fc3/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

run_match m1_tt_all_on "$B/tt_on/forge"  "" "$B/tt_off/forge" "" 7231 2000 700
run_match m2_bounds_on "$B/bounds/forge" "option.PvBoundFix=1 option.AspirationKeepExact=1" "$B/bounds/forge" "" 7232 2000 700
run_match m3_draw_tip  "$B/draw/forge"   "" "$B/base/forge"   "" 7233 2000 700
run_match m4_tt_st     "$B/tt_st/forge"  "" "$B/tt_off/forge" "" 7234 1500 520
run_match m5_tt_mc     "$B/tt_mc/forge"  "" "$B/tt_off/forge" "" 7235 1500 520
M6CAP=$(( $(date -u -d '2026-11-15T17:43:00Z' +%s) - $(date +%s) ))
run_match m6_tt_rs     "$B/tt_rs/forge"  "" "$B/tt_off/forge" "" 7236 1500 "$M6CAP"
echo "RUNNER_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
