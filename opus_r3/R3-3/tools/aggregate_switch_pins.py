"""Collect pins/switch_<head>_<name>.json (measure_pins.py outputs of run_switch_pins.sh or a single switch run)
into pins/switch_identity.json, keyed by exe key (nnueo2, nozero, speedstack, ttprefetch, lazyacc, int16).

Usage: python -I -B aggregate_switch_pins.py <pins_dir>
Each exe's sha256 is taken from the 'built <path> sha256 <hex>' line of the run logs pins/run_switch_pins_*.log.
"""
import glob
import json
import os
import re
import sys

AL1 = [312866, 862329, 3024920, 12389307, 34048354]
d = sys.argv[1]
built = {}
for lg in glob.glob(os.path.join(d, 'run_switch_pins_*.log')):
    for m in re.finditer(r'^built (\S+) sha256 ([0-9a-f]{64})', open(lg).read(), re.M):
        built[os.path.basename(m.group(1))] = m.group(2)
out = {}
for p in sorted(glob.glob(os.path.join(d, 'switch_*_*.json'))):
    if os.path.basename(p) == 'switch_identity.json':
        continue
    m = re.match(r'switch_([0-9a-f]{8})_(\w+)\.json$', os.path.basename(p))
    if not m:
        continue
    head, name = m.group(1), m.group(2)
    r = json.load(open(p))
    exe = os.path.basename(r['exe'])
    ent = {'head': head, 'exe': exe, 'exe_sha256': built.get(exe, ''), 'off': r['runs']['OFF']['pins']}
    if 'ON' in r['runs']:
        ent['on'] = r['runs']['ON']['pins']
        ent['on_options'] = r['runs']['ON']['options']
        ent['on_info'] = sorted({s for row in r['runs']['ON']['rows'] for s in row['info_strings']})[:4]
    ent['off_equals_AL1'] = ent['off'] == AL1
    ent['on_equals_AL1'] = (ent['on'] == AL1) if 'on' in ent else None
    out[name] = ent
    print(name, head, 'OFF=AL1' if ent['off_equals_AL1'] else 'OFF!=AL1', ent.get('on'), ent['exe_sha256'][:16])
json.dump(out, open(os.path.join(d, 'switch_identity.json'), 'w', newline='\n'), indent=1)
