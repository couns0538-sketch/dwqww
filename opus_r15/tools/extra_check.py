#!/usr/bin/env python3
"""extra_check.py - Opus R15: checks for an EXISTING exe whose option was never gated alone (no new build).

usage: python -I -B extra_check.py --name x --exe SRC.exe --option Name --on V [--note text] [--root D:\\o15\\cands]
                                   [--branch-dir D:\\o15\\wt\\opus_r15\\cands] [--smoke-seconds 120]

Copies SRC.exe into <root>/<name>/ (the crew's own file is only read; the copy's sha256 must equal the source's), then
pin_check OFF (-Full: bench d11-d22 + perft = lock pins) and ON (-Full -Options Name=V: advertised, in range, live,
perft = pins), smoke2m ON (120 s, Threads 2), and writes <root>/<name>/RESULT.json (kind "extra") + make_index.py.
Exit 0 = all checks PASS, 1 = a check failed, 2 = usage (existing record, missing exe).
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(path, algo='sha256'):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--exe', required=True)
    ap.add_argument('--option', required=True)
    ap.add_argument('--on', required=True)
    ap.add_argument('--note', default='')
    ap.add_argument('--root', default=r'D:\o15\cands')
    ap.add_argument('--branch-dir', default=r'D:\o15\wt\opus_r15\cands')
    ap.add_argument('--smoke-seconds', type=int, default=120)
    a = ap.parse_args()
    out = os.path.join(a.root, a.name)
    if os.path.exists(os.path.join(out, 'RESULT.json')):
        print(f'extra_check: {out}\\RESULT.json exists (never overwritten)', file=sys.stderr)
        return 2
    if not os.path.isfile(a.exe):
        print(f'extra_check: exe not found: {a.exe}', file=sys.stderr)
        return 2
    os.makedirs(out, exist_ok=True)
    exe = os.path.join(out, os.path.basename(a.exe))
    if os.path.exists(exe):
        print(f'extra_check: {exe} exists (never overwritten)', file=sys.stderr)
        return 2
    t0 = datetime.datetime.now()
    shutil.copyfile(a.exe, exe)
    checks, problems = {}, []

    def check(k, ok, detail):
        checks[k] = {'ok': bool(ok), 'detail': detail}
        if not ok:
            problems.append(f'{k}: {detail}')
        print(f"check {k:<16} {'PASS' if ok else 'FAIL'}  {detail}", flush=True)

    src_sha, copy_sha = sha(a.exe), sha(exe)
    check('copy_sha256', src_sha == copy_sha, f'source {src_sha} copy {copy_sha}')
    pin = os.path.join(HERE, 'pin_check.ps1')
    ps = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', pin, '-Exe', exe, '-Full']
    r = subprocess.run(ps + ['-Json', os.path.join(out, 'pin_off.json')], capture_output=True, text=True)
    check('pin_off', r.returncode == 0, 'bench d11-d22 + perft = lock pins')
    r = subprocess.run(ps + ['-Options', f'{a.option}={a.on}', '-Json', os.path.join(out, 'pin_on.json')], capture_output=True, text=True)
    check('pin_on_live', r.returncode == 0, f'{a.option}={a.on} advertised, accepted, live, perft = pins')
    pin_on = {}
    if os.path.exists(os.path.join(out, 'pin_on.json')):
        pin_on = json.load(open(os.path.join(out, 'pin_on.json'), encoding='utf-8-sig')).get('bench', {})
    r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'smoke2m.py'), exe, '--line', f'{a.option}={a.on}',
                        '--seconds', str(a.smoke_seconds), '--threads', '2', '--mask', '0x3', '--idle',
                        '--out', os.path.join(out, 'smoke_on')], capture_output=True, text=True)
    sm = json.load(open(os.path.join(out, 'smoke_on.json'), encoding='utf-8')) if os.path.exists(os.path.join(out, 'smoke_on.json')) else {}
    check('smoke', sm.get('verdict') == 'PASS', f"{sm.get('games')} games, {sm.get('plies')} plies, illegal {sm.get('illegal')}, "
                                                 f"crashes {sm.get('crashes')}, hangs {sm.get('hangs')}, time losses {sm.get('time_losses')}")
    res = {'tool': 'extra_check.py', 'kind': 'extra', 'name': a.name, 'option': a.option, 'on': a.on, 'note': a.note,
           'source_exe': a.exe, 'exe': exe, 'exe_sha256': copy_sha, 'exe_md5': sha(exe, 'md5'), 'checks': checks,
           'pin_on': pin_on, 'smoke': {k: sm.get(k) for k in ('verdict', 'seconds', 'threads', 'tc', 'games', 'plies',
                                                              'illegal', 'crashes', 'hangs', 'time_losses', 'overruns')},
           'problems': problems, 'verdict': 'PASS' if not problems else 'FAIL',
           'started': t0.strftime('%Y-%m-%d %H:%M:%S'), 'ended': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    text = json.dumps(res, indent=1) + '\n'
    with open(os.path.join(out, 'RESULT.json'), 'w', newline='\n') as f:
        f.write(text)
    bd = os.path.join(a.branch_dir, a.name, 'logs')
    os.makedirs(bd, exist_ok=True)
    for fn in ('RESULT.json', 'pin_off.json', 'pin_on.json', 'smoke_on.json'):
        if os.path.exists(os.path.join(out, fn)):
            shutil.copyfile(os.path.join(out, fn), os.path.join(bd, fn))
    subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'make_index.py'), '--root', a.root, '--copy-to', a.branch_dir])
    print(f"extra_check {res['verdict']} {a.name}")
    return 0 if not problems else 1


if __name__ == '__main__':
    sys.exit(main())
