#!/usr/bin/env bash
# collect_w3.sh - Opus 30-h job, end of window 3: print every final number the report needs (read-only): the run and
# sanity tables (w2_tables.py), the pooled matches of nets that played twice (combine_sanity.py), the soups of the
# window (soup_table.py rows), and gate_summary.py's forfeit / illegal / crash line of every match of windows 2-3.
set -u
A=/d/o30/wt/opus_30h/a; T=/d/o30/wt/opus_30h/tools; PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
N=/d/o30/nets
echo "== tables $(date '+%F %T')"
"$PY" -I -B "$A/w2_tables.py"
echo; echo "== pooled matches (both opening sets; SANITY ONLY)"
for n in o30_gpu_soupU8r3r5r10r12r14 o30_gpu_kb8short_r5; do
    [ -f "$N/$n/sanity2/sanity2.log" ] && "$PY" -I -B "$A/combine_sanity.py" "$N/$n/sanity/sanity.log" "$N/$n/sanity2/sanity2.log" | tail -1 | sed "s#^#$n #"
done
echo; echo "== soups of window 3 (C:/o30g/gpu/soups)"
"$PY" -I -B "$A/soup_table.py" 2>/dev/null | grep -E '_w3|^\| soup \|'
echo; echo "== match hygiene (gate_summary.py)"
for d in "$N"/o30_gpu_*/sanity*; do
    [ -f "$d/$(basename "$d").log" ] || continue   # sanity_match.py names the log after its folder
    printf '%s: %s\n' "${d#$N/}" "$("$PY" -I -B "$T/gate_summary.py" "$(cygpath -w "$d")" 2>&1 | grep -E '^time forfeits' | cut -c1-110)"
done
