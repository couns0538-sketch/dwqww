#!/usr/bin/env bash
# kb8b_candidate.sh - Opus 30-h job, window 2: after run 15 (KB8, 600 superbatches) is scored, score two KB8 soups with
# it, pack the better one (best S31 among those with jobA z <= -2, else best S31) and name it for the CPU 0 match
# (C:/o30g/gpu/cpu0_candidate.txt). Fallback: anything fails -> the parked name (Z32) is restored, so CPU 0 never idles.
# Why: in the sanity matches the KB8 net (run 5, 52.6 % / 400 games) reads at least as well as the slower layouts, and
# KB8 costs no engine speed vs KB4 (single run).
set -u
A=/d/o30/wt/opus_30h/a; S=$A/soup_score.sh; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
fallback() { cp /c/o30g/gpu/cpu0_candidate.hold /c/o30g/gpu/cpu0_candidate.txt; echo "$(date '+%F %T') FALLBACK: $1 -> CPU 0 gets $(cat /c/o30g/gpu/cpu0_candidate.txt)"; exit 3; }
until [ -f /c/o30g/gpu/r15_kb8long2_nets/forge_v2r_rank4x2_h256-600.done ]; do
    [ "$(date +%H%M)" -ge 1755 ] && fallback "run 15 not scored by 17:55"
    sleep 15
done
echo "$(date '+%F %T') r15 scored: $(tail -1 /c/o30g/gpu/r15_kb8long2_scores.tsv | cut -f1,4,5,7,8)"
G3=/d/o30/gpu/r3_kb8warm/forge_v2r_rank4x2_h256-700/quantised.bin
G5=/d/o30/gpu/r5_kb8short/forge_v2r_rank4x2_h256-200/quantised.bin
G10=/c/o30g/gpu/r10_kb8seed2/forge_v2r_rank4x2_h256-200/quantised.bin
G12=/c/o30g/gpu/r12_kb8long/forge_v2r_rank4x2_h256-600/quantised.bin
G14=/c/o30g/gpu/r14_kb8m400lr15/forge_v2r_rank4x2_h256-400/quantised.bin
G15=/c/o30g/gpu/r15_kb8long2/forge_v2r_rank4x2_h256-600/quantised.bin
cd /c/o30g/exp || fallback "no exp folder"
O30_MASK=0x38 bash "$S" soupX8_r3_r5_r12_r14_r15 rank4x2 "$G3" "$G5" "$G12" "$G14" "$G15" > X8.out 2>&1
O30_MASK=0x38 bash "$S" soupY8_r3_r5_r10_r12_r14_r15 rank4x2 "$G3" "$G5" "$G10" "$G12" "$G14" "$G15" > Y8.out 2>&1
best=$("$PY" -I -B - <<'EOF'
import csv
rows = []
for name in ('soupX8_r3_r5_r12_r14_r15', 'soupY8_r3_r5_r10_r12_r14_r15'):
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
echo "$(date '+%F %T') soups: $(tail -1 /c/o30g/gpu/soups/soupX8_r3_r5_r12_r14_r15_scores.tsv | cut -f1,4,5,7,8) | $(tail -1 /c/o30g/gpu/soups/soupY8_r3_r5_r10_r12_r14_r15_scores.tsv | cut -f1,4,5,7,8); chosen: $best"
[ -n "$best" ] || fallback "no soup scored"
short=$(echo "$best" | sed 's/^soup\([A-Z]8\)_/\1_/; s/_//g')
pack=o30_gpu_soup$short
cd /d/o30 && O30_MASK=0x38 bash "$A/net_pack.sh" "$pack" "/c/o30g/gpu/soups/${best}_nets/${best}-1.nnue2" \
    /d/o30/w/v2p4_pc1/src_copy/forge_ltopgo_v2p4_pc1.exe /d/o30/harness/h1 > "/d/o30/logs/net_pack_$pack.out" 2>&1 \
    || fallback "net_pack $pack failed"
echo "$pack" > /c/o30g/gpu/cpu0_candidate.txt
echo "$(date '+%F %T') named $pack for CPU 0 (400 games)"
