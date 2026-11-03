#!/usr/bin/env python3
"""report_rows.py - Opus R15: Markdown tables for FINAL_REPORT.md straight from the records (no hand-copied hashes).

usage: python -I -B report_rows.py [--root D:\\o15\\cands]
Prints (1) the candidate table (exe path, sha256, md5, setoption, ON bench d11-d22, patch sha256), (2) the check table
(every cand_pack check, the R13 cand_checks result, the fixed-clock smoke, CI run) and (3) the extras table.
"""
import argparse
import glob
import json
import os


def load(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'D:\o15\cands')
    a = ap.parse_args()
    recs = []
    for p in sorted(glob.glob(os.path.join(a.root, '*', 'RESULT.json'))):
        r = load(p)
        if r:
            r['_dir'] = os.path.dirname(p)
            recs.append(r)
    cands = [r for r in recs if r.get('kind', 'candidate') == 'candidate' and r.get('option')]
    extras = [r for r in recs if r.get('kind') == 'extra']
    print('| line | setoption | exe (full path) | sha256 | md5 | ON bench d11 / d13 / d16 / d20 / d22 | patch sha256 |')
    print('|---|---|---|---|---|---|---|')
    for r in cands:
        on = r.get('pin_on') or {}
        print(f"| {r['name']} | `{r['option']} {r['on']}` | `{r['exe']}` | `{r['exe_sha256']}` | `{r['exe_md5']}` | "
              + ' / '.join(str(on.get(k, '?')) for k in ('d11', 'd13', 'd16', 'd20', 'd22'))
              + f" | `{r.get('patch_sha256', '')}` |")
    print()
    keys = ['patch_applies', 'cleanroom_lint', 'kit_build', 'pc1_equals_pc2', 'kit_identity', 'kit_vfmadd0',
            'kit_missing_profile0', 'kit_on_live', 'exe_copy_sha256', 'pin_off', 'pin_on_live', 'smoke']
    print('| line | ' + ' | '.join(keys) + ' | smoke (fixed clock) | R13 cand_checks | CI |')
    print('|---|' + '---|' * (len(keys) + 3))
    for r in cands:
        c = r.get('checks', {})
        cells = ['PASS' if c.get(k, {}).get('ok') else ('-' if k not in c else 'FAIL') for k in keys]
        sm = load(os.path.join(r['_dir'], 'smoke_fixedclock.json'))
        smt = (f"{sm['verdict']} {sm['games']} g / {sm['illegal']} ill / {sm['crashes']} cr" if sm else 'n/a')
        cc = load(os.path.join(r['_dir'], 'cand_checks.json'))
        cct = 'n/a'
        if cc:
            cct = 'PASS' if cc.get('pass', cc.get('ok')) else 'FAIL'
            if isinstance(cc.get('mate'), dict):
                cct += ' (mate probe ' + ', '.join(f'{k} {v}' for k, v in cc['mate'].items() if isinstance(v, (int, str)))[:80] + ')'
        ci = load(os.path.join(r['_dir'], 'ci.json')) or {}
        print(f"| {r['name']} | " + ' | '.join(cells) + f" | {smt} | {cct} | {ci.get('conclusion', '?')} {ci.get('run', '')} |")
    print()
    print('| extra | setoption | exe (full path) | sha256 | md5 | ON bench d11 / d13 / d16 | verdict |')
    print('|---|---|---|---|---|---|---|')
    for r in extras:
        on = r.get('pin_on') or {}
        print(f"| {r['name']} | `{r['option']} {r['on']}` | `{r['exe']}` | `{r['exe_sha256']}` | `{r['exe_md5']}` | "
              + ' / '.join(str(on.get(k, '?')) for k in ('d11', 'd13', 'd16')) + f" | {r.get('verdict')} |")


if __name__ == '__main__':
    main()
