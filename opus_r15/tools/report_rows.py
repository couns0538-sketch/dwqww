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
        if sm:
            smt = f"{sm['verdict']} {sm['games']} g / {sm['illegal']} ill / {sm['crashes']} cr"
        elif r.get('started', '') >= '2026-11-03 12:38' and r.get('smoke'):
            ps = r['smoke']   # packed after the 12:37 clock fix: the pack's own smoke used the fixed tool
            smt = f"{ps.get('verdict')} {ps.get('games')} g / {ps.get('illegal')} ill / {ps.get('crashes')} cr (pack smoke)"
        else:
            smt = 'n/a'
        cc = load(os.path.join(r['_dir'], 'cand_checks.json'))
        cct = 'n/a'
        if cc:
            s = cc.get('summary') or {}
            legal = all(x.get('legal') for x in (cc.get('checks') or {}).get('smoke', []))
            cct = (f"T1/T4 {'legal' if legal else 'ILLEGAL'}; mates at 3M OFF {s.get('OFF')} / ON "
                   f"{s.get(r['option'] + '=' + r['on'])}")
            mr = load(os.path.join(r['_dir'], 'mate_reprobe.json'))
            if mr and mr['flips']:
                kinds = [f['verdict'] for f in mr['flips']]
                allh = all(k.startswith('horizon') for k in kinds)
                cct += (f"; {len(kinds)} flip(s) re-probed at 30M: " +
                        ('all horizon flips, both solve them' if allh else '; '.join(kinds)))
            elif not cc.get('fail'):
                cct += '; no flips'
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
