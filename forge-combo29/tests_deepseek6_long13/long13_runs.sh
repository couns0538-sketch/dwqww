#!/usr/bin/env bash
# long13_runs.sh -- the four counting runs, four probe runs, three controls (all with rows+capture).
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long13
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
STEPS=/tmp/l13_steps/build/forge
PROBE=/tmp/l13_probe/build/forge
O=$L1/first200.fens
G=$L1/set_G.epd
H=/tmp/ds6_work/forge-combo29/tests_deepseek6_long13/chkrun.py
mkdir -p "$J/runs"
run() { # $1 exe, $2 tag, $3 setfile, $4 suffix ("-" = no S14), $5 env
  local exe="$1" tag="$2" setf="$3" suffix="$4" envv="$5"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ "$suffix" = "-" ] && opts=""; [ -n "$suffix" ] && [ "$suffix" != "-" ] && [ "${suffix:0:1}" = "+" ] && opts="${suffix:1}"; [ -n "$suffix" ] && [ "$suffix" != "-" ] && [ "${suffix:0:1}" != "+" ] && [ "$suffix" != "-" ] && opts="${S14};${suffix}"
  env $envv python3 "$H" --exe "$exe" --set "$setf" --out "$J/runs/$tag.rows" \
    --chk "$J/runs/$tag.nst" --depth 12 --opts "$opts" --meta "$J/runs/$tag.rows.meta" \
    > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
run "$STEPS" "c_def_O" "$O" "-" ""
run "$STEPS" "c_s14_O" "$O" "" ""
run "$STEPS" "c_s14_G" "$G" "" ""
run "$STEPS" "c_def_G" "$G" "-" ""
run "$PROBE" "r1_def_O" "$O" "-" ""
run "$PROBE" "r2_s14_O" "$O" "" ""
run "$PROBE" "r3_s14_G" "$G" "" ""
run "$PROBE" "r4_def_G" "$G" "-" ""
run "$PROBE" "r5_rfp10_O" "$O" "+RfpMargin=10" ""
run "$PROBE" "r6_rfp300_O" "$O" "+RfpMargin=300" ""
run "$PROBE" "r7_rfp300N100_O" "$O" "+RfpMargin=300" "N_RFP=100"
echo "LONG13 RUNS DONE $(date -u)"
