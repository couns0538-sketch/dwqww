#!/usr/bin/env bash
# final_soups3b.sh - Opus 30-h job, end of GPU window 3, after final_soups3.sh: the KB32 soups that need r25 (a KB32
# seed since the 19:56 plan change, so final_soups3.sh - started before the change - leaves it out): Z32's five members
# + r24 + r25 (soupZ32c_w3), and the three native KB32 seed runs alone, r8 + r24 + r25 (soupN32_w3). Offline only.
# Waits for r25's last checkpoint to be scored and for final_soups3.sh to end (one soup scoring at a time on CPUs
# 5-6); stops waiting at 21:45.
set -u
A=/d/o30/wt/opus_30h/a; S=$A/soup_score.sh; G=/c/o30g/gpu; X=/c/o30g/exp
. "$A/../tools/idle.sh"; O30_MASK=0x60 o30_pin_self 0x60 >/dev/null || exit 78
late() { [ "$(date +%H%M)" -ge 2145 ]; }
r25=$G/r25_kb32s200c/forge_v2r_rank4x8_h256-200
until [ -f "$G/r25_kb32s200c_nets/forge_v2r_rank4x8_h256-200.done" ]; do late && { echo "$(date '+%T') r25 not scored by 21:45"; exit 3; }; sleep 15; done
until grep -q 'final_soups3 done' "$G/final_soups3.log" 2>/dev/null; do late && { echo "$(date '+%T') final_soups3 not done by 21:45"; break; }; sleep 15; done
r24=$G/r24_kb32s200b/forge_v2r_rank4x8_h256-200
r8=$G/r8_kb32short/forge_v2r_rank4x8_h256-200
for f in "$r24/quantised.bin" "$r25/quantised.bin" "$r8/quantised.bin"; do [ -f "$f" ] || { echo "missing $f"; exit 2; }; done
echo "$(date '+%F %T') r24 / r25 scored"
cd "$X" || exit 1
O30_MASK=0x60 bash "$S" soupZ32c_w3 rank4x8 "$X/r3.bin" "$X/r5.bin" "$X/r7.bin" "$r8/quantised.bin" "$X/r12.bin" \
    "$r24/quantised.bin" "$r25/quantised.bin" > Z32c.out 2>&1
echo "Z32c (7 members): $(tail -2 Z32c.out | head -1 | cut -f2,4,5,6,7,8)"
O30_MASK=0x60 bash "$S" soupN32_w3 rank4x8 "$r8/quantised.bin" "$r24/quantised.bin" "$r25/quantised.bin" > N32.out 2>&1
echo "N32 (r8 + r24 + r25): $(tail -2 N32.out | head -1 | cut -f2,4,5,6,7,8)"
echo "$(date '+%F %T') final_soups3b done"
