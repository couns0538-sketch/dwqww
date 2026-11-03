#!/usr/bin/env python3
"""readme_checks.py - Opus R15: append (or refresh) a "Check results" section in each candidate README from the records.

usage: python -I -B readme_checks.py [--root D:\\o15\\cands] [--branch D:\\o15\\wt\\opus_r15\\cands] NAME [NAME ...]
The section is everything after the line "## Check results (generated)"; it is rebuilt from RESULT.json,
smoke_fixedclock.json, cand_checks.json (R13) and mate_reprobe.json. Text above that line is never touched.
"""
import argparse
import json
import os

MARK = '## Check results (generated)'


def load(p):
    try:
        with open(p, encoding='utf-8-sig') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='+')
    ap.add_argument('--root', default=r'D:\o15\cands')
    ap.add_argument('--branch', default=r'D:\o15\wt\opus_r15\cands')
    a = ap.parse_args()
    for name in a.names:
        d = os.path.join(a.root, name)
        r = load(os.path.join(d, 'RESULT.json'))
        if not r:
            print(f'{name}: no RESULT.json, skipped')
            continue
        on = r.get('pin_on') or {}
        lines = [MARK, '',
                 f"- exe `{r['exe']}` sha256 `{r['exe_sha256']}` md5 `{r['exe_md5']}`; kit pc1 = pc2 "
                 f"`{(r.get('kit_exe_sha256') or {}).get('pc2', '')}`",
                 '- ON bench d11 / d13 / d16 / d20 / d22: ' + ' / '.join(str(on.get(k, '?')) for k in ('d11', 'd13', 'd16', 'd20', 'd22'))
                 + '; OFF = the lock pins; perft 4865609 / 193690690 both ways',
                 '- cand_pack checks: ' + ', '.join(f"{k} {'PASS' if v.get('ok') else 'FAIL'}" for k, v in r.get('checks', {}).items())]
        sm = load(os.path.join(d, 'smoke_fixedclock.json'))
        if sm:
            lines.append(f"- smoke with the fixed clock (12:37 fix): {sm['verdict']} - {sm['games']} games, {sm['plies']} plies, "
                         f"illegal {sm['illegal']}, crashes {sm['crashes']}, hangs {sm['hangs']}, time losses {sm['time_losses']}")
        cc = load(os.path.join(d, 'cand_checks.json'))
        if cc:
            s = cc.get('summary') or {}
            lines.append(f"- R13 cand_checks (T1 / T4 movetime smoke with perft-1 legality, mate probe 22 positions at 3M nodes): "
                         f"{cc.get('result')}; mates OFF {s.get('OFF')} / ON {s.get(r['option'] + '=' + r['on'])}; "
                         f"strict-rule flips: {'; '.join(cc.get('fail', [])) or 'none'}")
        mr = load(os.path.join(d, 'mate_reprobe.json'))
        if mr:
            for f in mr['flips']:
                lines.append(f"  - 30M re-probe ({f['kind']}) `{f['fen']}`: 3M OFF {f['off_3M']} / ON {f['on_3M']}; "
                             f"30M OFF {f['off_N']} / ON {f['on_N']} -> {f['verdict']}")
        ci = load(os.path.join(d, 'ci.json'))
        if ci:
            lines.append(f"- CI ASan+UBSan self-play: run {ci['run']} {ci['conclusion']} on {ci['commit'][:12]} (patch sha256 = the built one)")
        rd = os.path.join(a.branch, name, 'README.md')
        text = open(rd, encoding='utf-8').read()
        head = text.split(MARK)[0].rstrip('\n')
        with open(rd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(head + '\n\n' + '\n'.join(lines) + '\n')
        print(f'{name}: README check section written ({len(lines) - 2} lines)')


if __name__ == '__main__':
    main()
