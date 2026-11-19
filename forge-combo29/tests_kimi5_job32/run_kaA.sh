#!/bin/bash
# kimi5 job 32 known answer A: the class build's rows must equal the plain build's on O and G
# at go depth 12 (sums 8315168 | 17611204, against the committed job-29 plain rows) and at go
# nodes 20000 (fresh plain rows); the eight RANC classes must add up to the job-29 HP sums
# (O 4775611/11208, G 9106192/43280) and the RAN HP sums of the same files must match too.
set -u
J=/agent/repos/dwqww/forge-combo29/tests_kimi5_job32
J29=/agent/repos/dwqww/forge-combo29/tests_kimi5_job29
CLS=/tmp/j32/cls/build/forge
PLAIN=/tmp/j32/pc/build/forge
mkdir -p "$J/kaA"
run() { # exe go set tag
  local epd="$J/O.epd"; [ "$3" = G ] && epd="$J/G.epd"
  python3 "$J/runner_j32.py" "$1" "$epd" "$2" "$J/kaA" "$4" 100000 1 "$J/opts/base.opt" > "$J/kaA/$4.stdout" 2>&1
}
export J CLS PLAIN
export -f run
printf '%s\n' \
  "$CLS 'depth 12' O cls_O_d12" \
  "$CLS 'depth 12' G cls_G_d12" \
  "$CLS 'nodes 20000' O cls_O_n20000" \
  "$CLS 'nodes 20000' G cls_G_n20000" \
  "$PLAIN 'nodes 20000' O plain_O_n20000" \
  "$PLAIN 'nodes 20000' G plain_G_n20000" | \
  xargs -d '\n' -n 1 -P 4 bash -c 'eval run $0'
echo "== kaA runs done $(date -u) =="
python3 - "$J" "$J29" <<'PY'
import json, sys
J, J29 = sys.argv[1], sys.argv[2]
def load(p): return json.load(open(p))
co = load(f'{J}/kaA/cls_O_d12.json'); cg = load(f'{J}/kaA/cls_G_d12.json')
po = load(f'{J29}/rows/base_O_d12.json'); pg = load(f'{J29}/rows/base_G_d12.json')
print('cls O d12 sum', co['nodes_sum'], '== plain 8315168:', co['nodes_sum'] == 8315168,
      '| rows equal job29 plain:', co['per_position'] == po['per_position'] and co['bestmove'] == po['bestmove'])
print('cls G d12 sum', cg['nodes_sum'], '== plain 17611204:', cg['nodes_sum'] == 17611204,
      '| rows equal job29 plain:', cg['per_position'] == pg['per_position'] and cg['bestmove'] == pg['bestmove'])
for tag in ('cls_O_n20000', 'cls_G_n20000'):
    c = load(f'{J}/kaA/{tag}.json'); p = load(f'{J}/kaA/{tag.replace("cls", "plain")}.json')
    print(f'{tag} vs plain: rows equal:',
          c['per_position'] == p['per_position'] and c['bestmove'] == p['bestmove'],
          '| cls sum', c['nodes_sum'], '| plain sum', p['nodes_sum'])
def hp_sums(j):
    ranc = {}
    ran_hp = [0, 0]
    for search in j['ranc']:
        for cls, r, f in search:
            a = ranc.setdefault(cls, [0, 0]); a[0] += r; a[1] += f
    for search in j['ran']:
        ran_hp[0] += search['HP'][0]; ran_hp[1] += search['HP'][1]
    return ranc, ran_hp
for name, j, want in (('O', co, (4775611, 11208)), ('G', cg, (9106192, 43280))):
    ranc, ran_hp = hp_sums(j)
    tr = sum(v[0] for v in ranc.values()); tf = sum(v[1] for v in ranc.values())
    print(f'{name}: 8-class reached sum {tr} == job29 HP reached {want[0]}: {tr == want[0]}; '
          f'fired sum {tf} == {want[1]}: {tf == want[1]}; RAN HP of same files {ran_hp} match: {ran_hp == [want[0], want[1]]}')
PY
