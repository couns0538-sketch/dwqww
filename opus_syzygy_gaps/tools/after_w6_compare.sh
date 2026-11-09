#!/usr/bin/env bash
# after_w6_compare.sh <new tag> <frozen tag> - the compares of after_w6.sh again, from its finished row files. Run because the first version of after_w6.sh cut the compare's JSON at 300 characters,
# before its verdict field, so every compare counted as failed whatever it said. No engine runs. One line per compare; exit 1 if any is not IDENTICAL. Appends to out/builds/after_w6_<new tag>.txt.
set -u
J=/d/forge_jobs_20261107/opus1
T=$J/repo/opus_syzygy_gaps/tools
tag=$1; ftag=$2
O=$J/out/builds/after_w6_$tag.txt
I=$J/out/ident
fails=0
say() { echo "$*" | tee -a "$O"; }
same() {
  python -I -B "$T/compare_runs.py" "$2" "$3" > "$J/tmp/cmp_$$.json"
  r=$(python -I -B -c "import json,sys; d=json.load(open(sys.argv[1])); print(d['verdict'], 'rows', d['rows_a'], d['rows_b'], 'different', d['different'], 'invalid', d['invalid'], 'distinct', d['distinct_rows'], 'nodes', d['nodes_a'], d['nodes_b'])" "D:/forge_jobs_20261107/opus1/tmp/cmp_$$.json")
  say "$1: $r"
  case "$r" in IDENTICAL*) ;; *) fails=$((fails + 1));; esac
}
say "--- compares again, full verdicts ($(date))"
for s in net_on tb_roots tb_clock; do same "$s, options 0, against the w6 + port parent" "$I/w6p6_parent_$tag/$s.jsonl" "$I/w6p6_B_$tag/$s.jsonl"; done
for s in net_on tb_roots tb_clock; do same "$s, options 0, against the P6 parent 150374ff" "$I/parent_150374ff/$s.jsonl" "$I/w6p6_B_$tag/$s.jsonl"; done
for s in tb_roots tb_clock tb_promo tb_ep tb_rep tb_castle tb_clock100 boundary; do same "$s, all on, against the frozen P6 line" "$I/on_buildB_c$ftag/$s.jsonl" "$I/on_w6p6_B_$tag/$s.jsonl"; done
same "UBSan rows, boundary, all on, against the kit build's rows" "$I/on_w6p6_B_$tag/boundary.jsonl" "$J/out/san/w6_$tag/boundary.jsonl"
if [ "$fails" -eq 0 ]; then say "VERDICT after_w6 line, after the compares: ALL CHECKS PASS"; else say "VERDICT after_w6 line, after the compares: $fails NOT IDENTICAL"; fi
[ "$fails" -eq 0 ]
