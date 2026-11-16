#!/usr/bin/env bash
# long14_runs.sh -- R3 identity, R4a wiring control (wire8), R4b margins on O and G.
set -u
J=/tmp/ds6_work/forge-combo29/tests_deepseek6_long14
L1=/tmp/ds6_work/forge-combo29/tests_deepseek6_long1
S14=$(cat "$L1/s14.txt")
TUN=/tmp/l14_tun/build/forge
WIRE=/tmp/l14_wire/build/forge
O=$L1/first200.fens
G=$L1/set_G.epd
W8=/tmp/wire8.fens
mkdir -p "$J/runs"
run() { # $1 exe, $2 tag, $3 setfile, $4 depth, $5 suffix
  local exe="$1" tag="$2" setf="$3" depth="$4" suffix="$5"
  [ -s "$J/runs/$tag.rows" ] && { echo "skip $tag"; return; }
  local opts="$S14"; [ -n "$suffix" ] && opts="${S14};${suffix}"
  python3 "$L1/rows.py" --exe "$exe" --set "$setf" --out "$J/runs/$tag.rows" --depth "$depth" \
    --opts "$opts" --meta "$J/runs/$tag.rows.meta" > "$J/runs/$tag.run.log" 2>&1
  echo "done $tag rc=$?"
}
run "$TUN" "r3_O" "$O" 12 ""
run "$TUN" "r3_G" "$G" 12 ""
run "$WIRE" "r4a_m0" "$W8" 12 "AspCappedReopen=true;AspReopenMargin=0"
run "$WIRE" "r4a_m13" "$W8" 12 "AspCappedReopen=true;AspReopenMargin=13"
run "$WIRE" "r4a_m100" "$W8" 12 "AspCappedReopen=true;AspReopenMargin=100"
run "$TUN" "r4b_m0_O" "$O" 12 "AspReopenMargin=0"
run "$TUN" "r4b_m100_O" "$O" 12 "AspReopenMargin=100"
run "$TUN" "r4b_m0_G" "$G" 12 "AspReopenMargin=0"
run "$TUN" "r4b_m100_G" "$G" 12 "AspReopenMargin=100"
echo "LONG14 RUNS DONE $(date -u)"
