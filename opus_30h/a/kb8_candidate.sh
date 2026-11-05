#!/usr/bin/env bash
# kb8_candidate.sh - Opus 30-h job, window 2: after run 14 (KB8) is scored, score two KB8 soups, pack the better one
# (best S31 among those with jobA z <= -2, else best S31) with net_pack.sh on CPUs 3-5 and name it for the CPU 2
# sanity match (C:/o30g/gpu/cpu2_candidate.txt). KB8 costs no engine speed vs KB4 (layout_rank4x2_vs_kb4.txt).
set -u
A=/d/o30/wt/opus_30h/a; S=$A/soup_score.sh; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
until [ -f /c/o30g/gpu/r14_kb8m400lr15_nets/forge_v2r_rank4x2_h256-400.done ]; do sleep 20; done
echo "$(date '+%F %T') r14 scored"
G3=/d/o30/gpu/r3_kb8warm/forge_v2r_rank4x2_h256-700/quantised.bin
G5=/d/o30/gpu/r5_kb8short/forge_v2r_rank4x2_h256-200/quantised.bin
G10=/c/o30g/gpu/r10_kb8seed2/forge_v2r_rank4x2_h256-200/quantised.bin
G12=/c/o30g/gpu/r12_kb8long/forge_v2r_rank4x2_h256-600/quantised.bin
G14=/c/o30g/gpu/r14_kb8m400lr15/forge_v2r_rank4x2_h256-400/quantised.bin
cd /c/o30g/exp || exit 1
O30_MASK=0x38 bash "$S" soupT8_r3_r5_r12_r14 rank4x2 "$G3" "$G5" "$G12" "$G14" > T8.out 2>&1
O30_MASK=0x38 bash "$S" soupU8_r3_r5_r10_r12_r14 rank4x2 "$G3" "$G5" "$G10" "$G12" "$G14" > U8.out 2>&1
best=$("$PY" -I -B - <<'EOF'
import csv
rows = []
for name in ('soupT8_r3_r5_r12_r14', 'soupU8_r3_r5_r10_r12_r14'):
    try:
        r = list(csv.DictReader(open(f'C:/o30g/gpu/soups/{name}_scores.tsv', encoding='utf-8'), delimiter='\t'))[-1]
        rows.append((name, float(r['paired_s31']), float(r['z_jobA'])))
    except (OSError, IndexError, KeyError, ValueError) as error:
        print(f'# {name}: no score ({type(error).__name__})')
good = [r for r in rows if r[2] <= -2] or rows
print(min(good, key=lambda r: r[1])[0] if good else '')
EOF
)
best=$(echo "$best" | grep -v '^#' | tail -1)
echo "$(date '+%F %T') soups: $(tail -1 /c/o30g/gpu/soups/soupT8_r3_r5_r12_r14_scores.tsv | cut -f1,4,5,7,8) | $(tail -1 /c/o30g/gpu/soups/soupU8_r3_r5_r10_r12_r14_scores.tsv | cut -f1,4,5,7,8); chosen: $best"
[ -n "$best" ] || { echo "no soup scored: no candidate"; exit 2; }
short=$(echo "$best" | sed 's/^soup\([A-Z]8\)_/\1_/; s/_//g')
pack=o30_gpu_soup$short
cd /d/o30 && O30_MASK=0x38 bash "$A/net_pack.sh" "$pack" "/c/o30g/gpu/soups/${best}_nets/${best}-1.nnue2" \
    /d/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe /d/o30/harness/h1 > "/d/o30/logs/net_pack_$pack.out" 2>&1
rc=$?
echo "$(date '+%F %T') net_pack $pack exit $rc: $(tail -1 "/d/o30/logs/net_pack_$pack.out" | cut -c1-160)"
[ "$rc" = 0 ] || { echo "pack failed: no candidate named"; exit 3; }
echo "$pack" > /c/o30g/gpu/cpu2_candidate.txt
echo "$(date '+%F %T') named $pack for CPU 2"
