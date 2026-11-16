#!/usr/bin/env bash
# long9_san.sh -- the nine R4 settings over O under the clean ASan+UBSan build; 0 lines expected.
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long9
L8=/tmp/ds6_work/forge-combo29/tests_deepseek6_long8
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
EXE=/tmp/l9_san/build/forge
O=$L1/first200.fens
DS="LmrDeeperShallower=true"
mkdir -p "$J/san"
run() { # $1 tag, $2 opts-suffix
  local tag="$1" suffix="$2"
  [ -s "$J/san/$tag.rows" ] && { echo "skip $tag"; return; }
  python3 "$L8/sanrun.py" --exe "$EXE" --set "$O" --out "$J/san/$tag.rows" \
    --raw "/tmp/l9_$tag.rawlog" --opts "LmrDeeperShallower=true;${suffix}" --depth 12
  python3 "$L8/sancount.py" "$J/san/$tag.rows"
  rm -f "/tmp/l9_$tag.rawlog"
}
run k3   "LmrDeeperBase=100000;LmrShallowerBase=-100000"
run k4a  "LmrDeeperBase=20"
run k4b  "LmrDeeperDepthMul=4"
run k4c  "LmrShallowerBase=50"
run k4d  "LmrShallowerDepthMul=3"
run deep "LmrShallowerBase=-100000"
run flat "LmrShallowerBase=8;LmrShallowerDepthMul=0"
run half "LmrDeeperBase=20;LmrDeeperDepthMul=1"
run dbl  "LmrDeeperBase=80;LmrDeeperDepthMul=4"
echo "LONG9 SAN DONE $(date -u)"
