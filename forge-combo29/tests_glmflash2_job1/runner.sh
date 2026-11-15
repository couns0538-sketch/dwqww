#!/bin/bash
# glmflash2 job 1 match runner. Runs each switch ON vs OFF, same exe both sides.
# 20000 nodes/move, Threads=1, Hash=16, UHO_Lichess_4852_v1.epd, fixed seeds.
FC=/tmp/fastchess/fastchess
ENG=/tmp/forgebuild/forge
BOOK=/tmp/UHO_Lichess_4852_v1.epd
OUT=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job1/matches
STATS=/agent/repos/dwqww/forge-combo29/tests_glmflash2_job1/pgn_stats.py
mkdir -p "$OUT"

run_match() {
  name=$1; opt=$2; seed=$3; tmo=$4
  echo "START $name seed=$seed $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  timeout --kill-after=10 "$tmo" "$FC" \
    -engine cmd="$ENG" name=cand option.Threads=1 option.Hash=16 $opt \
    -engine cmd="$ENG" name=base option.Threads=1 option.Hash=16 \
    -each proto=uci nodes=20000 \
    -openings file="$BOOK" format=epd order=random \
    -srand "$seed" -rounds 750 -games 2 -repeat -concurrency 4 -recover \
    -ratinginterval 100 -pgnout file=/tmp/fc/$name.pgn min=true \
    > /tmp/fc/${name}_out.txt 2>&1
  sleep 2
  pkill -f forgebuild/forge 2>/dev/null
  sleep 1
  echo "END $name rc=$? $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
  tail -n 40 /tmp/fc/${name}_out.txt > "$OUT/${name}_fastchess_tail40.txt"
  python3 "$STATS" /tmp/fc/$name.pgn > "$OUT/${name}_lines.txt" 2>&1
  head -n 3 "$OUT/${name}_lines.txt"
}

run_match m1_threathistory      "option.ThreatHistory=true"        7203 560
run_match m3_lmrlateparentrelief "option.LmrLateParentRelief=true" 7205 560
run_match m4_lmrdeepershallower "option.LmrDeeperShallower=true"   7206 560
run_match m5_evasionordering    "option.EvasionOrdering=true"      7207 560
run_match m6_aspcappedreopen    "option.AspCappedReopen=true"      7208 560
echo "RUNNER_DONE $(date -u +%FT%TZ)" >> "$OUT/timeline.txt"
