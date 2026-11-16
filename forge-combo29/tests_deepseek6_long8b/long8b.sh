#!/usr/bin/env bash
# long8b.sh -- the LmrFine F-option sanitizer sweep the long-8b prediction names.
set -u
D=/agent/repos/base/forge-combo29/tests_deepseek6_long8b
R=/agent/repos/base/forge-combo29/tests_deepseek6_long8
S14=$(cat "$D/../tests_deepseek6_long1/s14.txt")
mkdir -p "$D/runs"
EXE=/agent/repos/work/l8/build-LmrFine/forge

run() { # tag, options
  local tag="$1" opts="$2"
  if [ -s "$D/runs/$tag.rows" ]; then echo "skip $tag"; return 0; fi
  echo "--- $tag $(date -u) ---"
  for setname in O G; do
    if [ "$setname" = O ]; then sf=$R/first200.fens; else sf=$R/set_G.epd; fi
    python3 $R/sanrun.py --exe "$EXE" --set "$sf" \
        --out "$D/runs/${tag}_${setname}.rows" --opts "$opts" --depth 10
    python3 $R/sancount.py "$D/runs/${tag}_${setname}.rows"
  done
}

run fine1   "$S14;LmrFine=1"
run rf0     "$S14;LmrFine=1;LmrRoundF=0"
run tpf2048 "$S14;LmrFine=1;LmrTtPvF=2048"
run nif0    "$S14;LmrFine=1;LmrNotImprovingF=0"
run cnf0    "$S14;LmrFine=1;LmrCutNodeF=0"
run tcf0    "$S14;LmrFine=1;LmrTtCaptureF=0"
run gcf0    "$S14;LmrFine=1;LmrGiveCheckF=0"
run icf0    "$S14;LmrFine=1;LmrInCheckF=0"
run caf0    "$S14;LmrFine=1;LmrCutoffAddF=0"
echo "LONG8B DONE $(date -u)"
