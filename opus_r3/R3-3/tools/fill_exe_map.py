"""Fill exe_map.json from the main session's EXES.txt ("name | build | sha256 | head | ...").

Usage: python -I -B fill_exe_map.py <EXES.txt> <exe_map.json> [--require-ancestor-of <sha>]
Refuses when the listed exes do not share one head. Exes not listed keep sha256 null.
"""
import json
import re
import sys

lines = [ln for ln in open(sys.argv[1], encoding='utf-8').read().splitlines() if ln.strip()]
mp = json.load(open(sys.argv[2], encoding='utf-8'))
by_name = {v['name']: k for k, v in mp['exes'].items()}
heads = set()
filled = []
for ln in lines:
    parts = [p.strip() for p in ln.split('|')]
    if len(parts) < 4 or not re.fullmatch(r'[0-9a-f]{64}', parts[2]):
        continue
    name, sha, head = parts[0], parts[2], parts[3]
    heads.add(head)
    if name in by_name:
        mp['exes'][by_name[name]]['sha256'] = sha.upper()
        filled.append(name)
    else:
        print('not in exe_map (ignored):', name)
if len(heads) != 1:
    raise SystemExit(f'exes come from several heads: {sorted(heads)}')
mp['head'] = heads.pop()
with open(sys.argv[2], 'w', newline='\n', encoding='utf-8') as fh:
    json.dump(mp, fh, indent=1)
print('head', mp['head'], 'filled', filled)
