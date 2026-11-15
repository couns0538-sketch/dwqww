#!/bin/bash
# glmflash2 job 2 runner. Control 2 (seed 7211), then M1..M5.
# Every match gets a cap; on cap the runner sends SIGINT (fastchess stops
# gracefully, counts its games, prints its summary). M5's cap is the remaining
# time to the absolute deadline 16:23:30Z so only the last match can be cut.
FC=/tmp/fastchess/fastchess
ENG=/tmp/forgebuild/forge
BOOK=/tmp/UHO_Lichess_4852_v1.epd
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job2/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job2/pgn_stats.py
mkdir -p "$OUT"

run_match() {
  name=$1; opt=$2; seed=$3; games=$4; cap=$5
  echo "START $name seed=$seed cap=${cap}s $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 $opt \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds $((games / 2)) -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/tmp/fc/$name.pgn min=true \
    > /tmp/fc/${name}_out.txt 2>&1 &
  FCPID=$!
  DEAD=$(( $(date +%s) + cap ))
  while kill -0 $FCPID 2>/dev/null && [ "$(date +%s)" -lt "$DEAD" ]; do sleep 10; done
  if kill -0 $FCPID 2>/dev/null; then
    kill -INT $FCPID
    for i in $(seq 1 12); do kill -0 $FCPID 2>/dev/null || break; sleep 5; done
    kill -9 $FCPID 2>/dev/null
  fi
  wait $FCPID 2>/dev/null
  pkill -f forgebuild/forge 2>/dev/null
  sleep 1
  echo "END $name $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 /tmp/fc/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /tmp/fc/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

run_match control2_7211 ""                                       7211  300 300
run_match m1_lmdeepershallower "option.LmrDeeperShallower=true"  7221 2000 780
run_match m2_lds_th "option.LmrDeeperShallower=true option.ThreatHistory=true" 7222 2000 780
run_match m3_all6 "option.LmrDeeperShallower=true option.ThreatHistory=true option.LmrSignedCorrection=true option.LmrLateParentRelief=true option.EvasionOrdering=true option.AspCappedReopen=true" 7223 2000 780
run_match m4_lds_lpr_lsc "option.LmrDeeperShallower=true option.LmrLateParentRelief=true option.LmrSignedCorrection=true" 7224 1500 580
M5CAP=$(( $(date -u -d '2026-11-15T16:23:30Z' +%s) - $(date +%s) ))
run_match m5_lds_th_eo_acr "option.LmrDeeperShallower=true option.ThreatHistory=true option.EvasionOrdering=true option.AspCappedReopen=true" 7225 1500 "$M5CAP"
echo "RUNNER_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
