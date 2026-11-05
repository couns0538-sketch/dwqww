#!/usr/bin/env bash
# final_soups.sh - Opus 30-h job, end of GPU window 2: offline soups with every finished run (no sanity match is
# possible any more inside the window; offline numbers only, selection-biased like every soup). Idle, CPUs 3-5.
set -u
A=/d/o30/wt/opus_30h/a; S=$A/soup_score.sh; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
X=/c/o30g/exp; G=/c/o30g/gpu
. "$A/../tools/idle.sh"; o30_pin_self 0x38 >/dev/null || exit 78
last=r20_kb8s100; [ -f "$G/$last.guard.log" ] || last=r19_kb8m300b
until grep -q ' end: ' "$G/$last.guard.log" 2>/dev/null; do sleep 15; done
ck() { ls -d "$G/$1"/forge_v2r_*-* 2>/dev/null | sort -t- -k2 -n | tail -1; }
until [ -f "$G/${last}_nets/$(basename "$(ck $last)").done" ]; do sleep 10; done
echo "$(date '+%F %T') last run $last scored"
KB8=( /d/o30/gpu/r3_kb8warm/forge_v2r_rank4x2_h256-700 /d/o30/gpu/r5_kb8short/forge_v2r_rank4x2_h256-200 )
for r in r10_kb8seed2 r12_kb8long r14_kb8m400lr15 r15_kb8long2 r16_kb8s200lr1 r17_kb8m300 r18_kb8s200lr3 r19_kb8m300b r20_kb8s100; do
    c=$(ck $r); [ -n "$c" ] && KB8+=("$c")
done
echo "KB8 members: ${#KB8[@]}"
q8=(); for c in "${KB8[@]}"; do q8+=("$c/quantised.bin"); done
cd "$X" || exit 1
O30_MASK=0x38 bash "$S" soupF8_all_kb8 rank4x2 "${q8[@]}" > F8.out 2>&1; echo "F8 all KB8 runs: $(tail -2 F8.out | head -1 | cut -f2,4,5,6,7,8)"
# KB8 without the lr 3e-5 run and the 100-superbatch run (both further from the recipe)
q8b=(); for c in "${KB8[@]}"; do case "$c" in *r18_*|*r20_*) ;; *) q8b+=("$c/quantised.bin");; esac; done
O30_MASK=0x38 bash "$S" soupG8_kb8_sel rank4x2 "${q8b[@]}" > G8.out 2>&1; echo "G8 KB8 without r18 / r20: $(tail -2 G8.out | head -1 | cut -f2,4,5,6,7,8)"
# KB16: V16 members + every KB8 run expanded to KB16
q16=(/d/o30/gpu/r7_kb16short/forge_v2r_rank4x4_h256-200/quantised.bin "$G/r11_kb16long/forge_v2r_rank4x4_h256-600/quantised.bin" "$G/r13_kb16m400lr15/forge_v2r_rank4x4_h256-400/quantised.bin")
i=0; for c in "${q8b[@]}"; do i=$((i+1)); o="$X/f16_$i.bin"; [ -e "$o" ] || "$PY" -I -B "$A/o30_expand_kb.py" --from rank4x2 --to rank4x4 "$(cygpath -w "$c")" "$(cygpath -w "$o")" > /dev/null; q16+=("$o"); done
O30_MASK=0x38 bash "$S" soupH16_all rank4x4 "${q16[@]}" > H16.out 2>&1; echo "H16 KB16 + KB8 expanded: $(tail -2 H16.out | head -1 | cut -f2,4,5,6,7,8)"
echo "$(date '+%F %T') final_soups done"
