#!/usr/bin/env bash
# identity_compare.sh <ref tag> <cand tag> - compare_runs.py over all identity sets in out/ident/<tag>/. Writes out/ident/<cand tag>/COMPARE.txt, exit 1 if any set is not IDENTICAL.
set -u
J=/d/forge_jobs_20261107/opus1
T=$J/repo/opus_syzygy_gaps/tools
R=$J/out/ident/$1
C=$J/out/ident/$2
O=$C/COMPARE.txt
rc=0
echo "ref $(head -1 "$R/RUN.txt" | cut -c1-200)" > "$O"
echo "cand $(head -1 "$C/RUN.txt" | cut -c1-200)" >> "$O"
for s in net_on net_off tb_12k tb_roots tb_clock tb_promo tb_ep tb_rep tb_castle tb_clock100; do
  if [ ! -e "$C/$s.jsonl" ]; then echo "$s MISSING" >> "$O"; rc=1; continue; fi
  line=$(python -I -B "$T/compare_runs.py" "$R/$s.jsonl" "$C/$s.jsonl" --json "$C/$s.compare.json") || rc=1
  echo "$s $(echo "$line" | python -I -B -c "import json,sys; r=json.loads(sys.stdin.read()); print(r['verdict'],'rows',r['rows_a'],'different',r['different'],'distinct',r['distinct_rows'],'nodes',r['nodes_a'],r['nodes_b'],r['examples'][:1])" | cut -c1-260)" >> "$O"
done
cat "$O" | cut -c1-200
exit $rc
