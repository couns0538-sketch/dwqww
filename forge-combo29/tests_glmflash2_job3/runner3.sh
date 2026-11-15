#!/bin/bash
# glmflash2 job 3 runner. C = control (per-engine nodes!), then M1..M6.
# Every match capped; cap reached -> SIGINT (verified graceful in job 2 prep).
FC=/tmp/fastchess/fastchess
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job3/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job3/pgn_stats.py
mkdir -p "$OUT"

run_match() {
  name=$1; cand_engine=$2; cand_opts=$3; cand_nodes=$4; base_engine=$5; base_opts=$6; base_nodes=$7; seed=$8; games=$9; cap=${10}
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$cand_engine" name=cand option.Threads=1 option.Hash=16 option.OwnBook=false $cand_opts $cand_nodes \
    -engine cmd="$base_engine" name=base option.Threads=1 option.Hash=16 option.OwnBook=false $base_opts $base_nodes \
    -each proto=uci \
    -openings file=/tmp/UHO_Lichess_4852_v1.epd format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/tmp/fc3/$name.pgn min=true \
    > /tmp/fc3/${name}_out.txt 2>&1 &
  FCPID=$!
  DEAD=$(( $(date +%s) + cap ))
  while kill -0 $FCPID 2>/dev/null && [ "$(date +%s)" -lt "$DEAD" ]; do sleep 10; done
  if kill -0 $FCPID 2>/dev/null; then
    kill -INT $FCPID
    for i in $(seq 1 12); do kill -0 $FCPID 2>/dev/null || break; sleep 5; done
    kill -9 $FCPID 2>/dev/null
  fi
  wait $FCPID 2>/dev/null
  pkill -f j3build 2>/dev/null
  sleep 1
  echo "END $name $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 /tmp/fc3/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /tmp/fc3/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

B=/tmp/j3build
mkdir -p /tmp/fc3
run_match control_7230   "$B/base/forge"   ""                                     "nodes=20000" "$B/base/forge"   "" "nodes=10000" 7230 300 300
run_match m1_tt_all_on   "$B/tt_on/forge"  ""                                     "nodes=20000" "$B/tt_off/forge" "" "nodes=20000" 7231 2000 700
run_match m2_bounds_on   "$B/bounds/forge" "option.PvBoundFix=1 option.AspirationKeepExact=1" "nodes=20000" "$B/bounds/forge" "" "nodes=20000" 7232 2000 700
run_match m3_draw_tip    "$B/draw/forge"   ""                                     "nodes=20000" "$B/base/forge"   "" "nodes=20000" 7233 2000 700
run_match m4_tt_st       "$B/tt_st/forge"  ""                                     "nodes=20000" "$B/tt_off/forge" "" "nodes=20000" 7234 1500 520
run_match m5_tt_mc       "$B/tt_mc/forge"  ""                                     "nodes=20000" "$B/tt_off/forge" "" "nodes=20000" 7235 1500 520
M6CAP=$(( $(date -u -d '2026-11-15T17:40:00Z' +%s) - $(date +%s) ))
run_match m6_tt_rs       "$B/tt_rs/forge"  ""                                     "nodes=20000" "$B/tt_off/forge" "" "nodes=20000" 7236 1500 "$M6CAP"
echo "RUNNER_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
