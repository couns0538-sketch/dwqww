#!/bin/bash
# kimi5 job 29 known answer A: the counting build's rows must equal the plain build's
# (O/G at depth 12; the 40 job-26 positions at depth 9 = 405,544).
set -u
J=/agent/repos/dwqww/forge-combo29/tests_kimi5_job29
CE=/tmp/b29cnt/build/forge
mkdir -p "$J/kaA"
python3 "$J/runner_j18.py" "$CE" "$J/O.epd" 12 "$J/kaA" cntbase_O_d12 100000 1 "$J/opts/base.opt" > "$J/kaA/cntbase_O_d12.stdout" 2>&1 &
python3 "$J/runner_j18.py" "$CE" "$J/G.epd" 12 "$J/kaA" cntbase_G_d12 100000 1 "$J/opts/base.opt" > "$J/kaA/cntbase_G_d12.stdout" 2>&1 &
python3 "$J/runner_j18.py" "$CE" "$J/O.epd" 9 "$J/kaA" cntbase_O20_d9 20 1 "$J/opts/base.opt" > "$J/kaA/cntbase_O20_d9.stdout" 2>&1 &
python3 "$J/runner_j18.py" "$CE" "$J/G.epd" 9 "$J/kaA" cntbase_G20_d9 20 1 "$J/opts/base.opt" > "$J/kaA/cntbase_G20_d9.stdout" 2>&1 &
wait
grep -c "info string RAN" "$J/kaA/cntbase_O_d12_full.txt"
python3 - "$J" <<'PY'
import json, sys
J = sys.argv[1]
o = json.load(open(f'{J}/kaA/cntbase_O_d12.json')); g = json.load(open(f'{J}/kaA/cntbase_G_d12.json'))
o9 = json.load(open(f'{J}/kaA/cntbase_O20_d9.json')); g9 = json.load(open(f'{J}/kaA/cntbase_G20_d9.json'))
print('cnt O d12', o['nodes_sum'], o['nodes_first3'])
print('cnt G d12', g['nodes_sum'], g['nodes_first3'])
print('cnt 40pos d9', o9['nodes_sum'] + g9['nodes_sum'])
po = json.load(open(f'{J}/rows/base_O_d12.json')); pg = json.load(open(f'{J}/rows/base_G_d12.json'))
print('O rows equal plain:', o['per_position'] == po['per_position'] and o['bestmove'] == po['bestmove'])
print('G rows equal plain:', g['per_position'] == pg['per_position'] and g['bestmove'] == pg['bestmove'])
PY
