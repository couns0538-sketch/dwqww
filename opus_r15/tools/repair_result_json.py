#!/usr/bin/env python3
"""repair_result_json.py - Opus R15 one-off: shrink RESULT.json records written before the 12:38 cand_pack fix.

usage: python -I -B repair_result_json.py RESULT.json [...]

PS 5.1 ConvertTo-Json wrote every kit SUMMARY line of `kit_summary` as an object carrying the line's PSPath / PSDrive /
PSProvider properties (about 20 MB per record, 35 MB files). This keeps only each line's text ("value"); every other
field, every check and every number is copied unchanged. The original is kept next to it as RESULT_35MB_original.json
(never deleted); a record without such objects is left alone. Prints old / new sizes and the fields compared.
"""
import json
import os
import sys

for path in sys.argv[1:]:
    with open(path, encoding='utf-8-sig') as f:
        r = json.load(f)
    ks = r.get('kit_summary') or []
    if not any(isinstance(x, dict) for x in ks):
        print(f'{path}: already plain ({os.path.getsize(path)} bytes), left alone')
        continue
    keep = os.path.join(os.path.dirname(path), 'RESULT_35MB_original.json')
    if os.path.exists(keep):
        sys.exit(f'{keep} exists: refusing to overwrite')
    new = dict(r)
    new['kit_summary'] = [x.get('value', '') if isinstance(x, dict) else x for x in ks]
    new['repaired'] = 'kit_summary lines reduced to their text by repair_result_json.py (2026-11-03); nothing else changed'
    same = all(new[k] == r[k] for k in r if k != 'kit_summary')
    if not same:
        sys.exit(f'{path}: a field other than kit_summary changed - refusing')
    old_size = os.path.getsize(path)
    os.rename(path, keep)
    with open(path, 'w', newline='\n', encoding='utf-8') as f:
        json.dump(new, f, indent=1)
        f.write('\n')
    print(f'{path}: {old_size} -> {os.path.getsize(path)} bytes; original kept as {keep}; '
          f'{len(new["kit_summary"])} summary lines; other fields identical')
