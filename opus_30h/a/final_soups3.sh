#!/usr/bin/env bash
# final_soups3.sh - Opus 30-h job, end of GPU window 3: when plan 3's queue has ended and the new runs' last checkpoints
# are scored, two offline soups: Y8's six members + the r5-recipe seeds r23 / r25 (KB8), and Z32's five members + r24
# (KB32). Offline numbers only (selection-biased like every soup; no time left for a sanity match). Idle on CPUs 5-6.
# A missing run (not started before the cutoff) is left out and said so; the script stops waiting at 21:40.
set -u
A=/d/o30/wt/opus_30h/a; S=$A/soup_score.sh; G=/c/o30g/gpu; X=/c/o30g/exp
. "$A/../tools/idle.sh"; O30_MASK=0x60 o30_pin_self 0x60 >/dev/null || exit 78
late() { [ "$(date +%H%M)" -ge "$1" ]; }
until grep -q -E 'queue ends' "$G/queue_runner3.log" 2>/dev/null; do late 2140 && { echo "$(date '+%T') 21:40: queue not ended"; break; }; sleep 20; done
last() { ls -d "$G/$1"/forge_v2r_*-* 2>/dev/null | sort -t- -k2 -n | tail -1; }
ready() {   # <run>: its last checkpoint is scored (.done) or the run never started
    local c; c=$(last "$1"); [ -z "$c" ] && return 0
    [ -f "$G/${1}_nets/$(basename "$c").done" ]
}
for r in r23_kb8s200b r24_kb32s200b r25_kb8s200c; do
    until ready "$r"; do late 2140 && { echo "$(date '+%T') 21:40: $r not scored"; break; }; sleep 15; done
done
echo "$(date '+%F %T') plan 3 runs scored"
q8=(/d/o30/gpu/r3_kb8warm/forge_v2r_rank4x2_h256-700/quantised.bin /d/o30/gpu/r5_kb8short/forge_v2r_rank4x2_h256-200/quantised.bin
    $G/r10_kb8seed2/forge_v2r_rank4x2_h256-200/quantised.bin $G/r12_kb8long/forge_v2r_rank4x2_h256-600/quantised.bin
    $G/r14_kb8m400lr15/forge_v2r_rank4x2_h256-400/quantised.bin $G/r15_kb8long2/forge_v2r_rank4x2_h256-600/quantised.bin)
for r in r23_kb8s200b r25_kb8s200c; do
    c=$(last "$r"); if [ -n "$c" ] && [ -f "$G/${r}_nets/$(basename "$c").done" ]; then q8+=("$c/quantised.bin"); else echo "left out: $r"; fi
done
q32=($X/r3.bin $X/r5.bin $X/r7.bin $G/r8_kb32short/forge_v2r_rank4x8_h256-200/quantised.bin $X/r12.bin)
c=$(last r24_kb32s200b); if [ -n "$c" ] && [ -f "$G/r24_kb32s200b_nets/$(basename "$c").done" ]; then q32+=("$c/quantised.bin"); else echo "left out: r24"; fi
cd "$X" || exit 1
O30_MASK=0x60 bash "$S" soupY8b_w3 rank4x2 "${q8[@]}" > Y8b.out 2>&1
echo "Y8b (${#q8[@]} members): $(tail -2 Y8b.out | head -1 | cut -f2,4,5,6,7,8)"
O30_MASK=0x60 bash "$S" soupZ32b_w3 rank4x8 "${q32[@]}" > Z32b.out 2>&1
echo "Z32b (${#q32[@]} members): $(tail -2 Z32b.out | head -1 | cut -f2,4,5,6,7,8)"
echo "$(date '+%F %T') final_soups3 done"
