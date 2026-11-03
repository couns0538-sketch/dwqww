#!/usr/bin/env python3
"""index_check.py - Opus R15: check every gate line of the candidate INDEX before the crew queues it.

usage: python -I -B index_check.py [--root D:\\o15\\cands] [--no-engine] [--json OUT]

For each <root>/<name>/RESULT.json (cand_pack.ps1 records and hand-written "extra" records):
  - the exe exists and its sha256 (and md5 when recorded) equals the record;
  - the record's verdict is PASS and every check in it passed;
  - the patch file (if any) exists and its sha256 equals the record;
  - a CI record (ci.json) exists with conclusion "success" (candidates only; extras were built in earlier rounds);
  - unless --no-engine: the exe's own `uci` answer advertises the option, its default is 0 / false, and the ON value
    lies inside the advertised min / max (the gate runner refuses options that are not advertised).
Exit 0 = every line OK, 1 = a line failed (each failure printed), 2 = usage.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys


def file_hash(path, algo):
    h = hashlib.new(algo)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def uci_options(exe):
    p = subprocess.run([exe], input='uci\nquit\n', capture_output=True, text=True, timeout=60)
    opts = {}
    for line in p.stdout.splitlines():
        m = re.match(r'option name (.+?) type (\w+)(?: default (\S+))?(?: min (-?\d+) max (-?\d+))?', line)
        if m:
            opts[m.group(1)] = {'type': m.group(2), 'default': m.group(3),
                                'min': int(m.group(4)) if m.group(4) else None,
                                'max': int(m.group(5)) if m.group(5) else None}
    return opts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'D:\o15\cands')
    ap.add_argument('--no-engine', action='store_true')
    ap.add_argument('--json', default='')
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.root, '*', 'RESULT.json')))
    if not paths:
        print(f'index_check: no RESULT.json under {a.root}', file=sys.stderr)
        return 2
    report, bad = [], 0
    for path in paths:
        fails = []
        try:
            with open(path, encoding='utf-8-sig') as f:
                r = json.load(f)
        except (OSError, ValueError) as e:
            print(f'FAIL {path}: unreadable ({e})')
            bad += 1
            continue
        name, kind = r.get('name', os.path.basename(os.path.dirname(path))), r.get('kind', 'candidate')
        if kind == 'candidate' and not r.get('option'):
            print(f'SKIP {name}: base run (no option line)')
            continue
        if kind == 'extra' and r.get('verdict') == 'FAIL':
            # a recorded finding (an existing exe whose line is not gateable), not a gate line: listed, never queued
            print(f"NOTE {name}: recorded as NOT gateable ({'; '.join(r.get('problems', []))[:160]})")
            report.append({'name': name, 'kind': kind, 'ok': None, 'failures': [], 'note': 'not gateable (finding)'})
            continue
        exe = r.get('exe', '')
        if not exe or not os.path.isfile(exe):
            fails.append(f'exe missing: {exe}')
        else:
            if file_hash(exe, 'sha256') != r.get('exe_sha256', '').lower():
                fails.append('exe sha256 differs from the record')
            if r.get('exe_md5') and file_hash(exe, 'md5') != r['exe_md5'].lower():
                fails.append('exe md5 differs from the record')
        if r.get('verdict') != 'PASS':
            fails.append(f"record verdict {r.get('verdict')}")
        for k, v in (r.get('checks') or {}).items():
            if not v.get('ok'):
                fails.append(f'check {k} failed in the record')
        if r.get('patch'):
            if not os.path.isfile(r['patch']):
                fails.append(f"patch missing: {r['patch']}")
            elif file_hash(r['patch'], 'sha256') != r.get('patch_sha256', '').lower():
                fails.append('patch sha256 differs from the record (patch edited after the build?)')
        if kind == 'candidate':
            ci = os.path.join(os.path.dirname(path), 'ci.json')
            if not os.path.exists(ci):
                fails.append('no ci.json (sanitizer CI not recorded)')
            else:
                with open(ci, encoding='utf-8-sig') as f:
                    c = json.load(f)
                if c.get('conclusion') != 'success':
                    fails.append(f"CI {c.get('run')} conclusion {c.get('conclusion')}")
        if not a.no_engine and exe and os.path.isfile(exe):
            try:
                opts = uci_options(exe)
            except (OSError, subprocess.TimeoutExpired) as e:
                opts = {}
                fails.append(f'uci failed: {e}')
            o = opts.get(r.get('option', ''))
            if o is None:
                fails.append(f"option {r.get('option')} not advertised by uci")
            else:
                if o['default'] not in ('0', 'false'):
                    fails.append(f"option {r['option']} default {o['default']} (must be 0 / false)")
                if o['min'] is not None:
                    try:
                        v = int(r.get('on'))
                        if not (o['min'] <= v <= o['max']):
                            fails.append(f"ON value {v} outside min {o['min']} max {o['max']}")
                    except (TypeError, ValueError):
                        fails.append(f"ON value {r.get('on')!r} is not an integer for a spin option")
        report.append({'name': name, 'kind': kind, 'ok': not fails, 'failures': fails})
        if fails:
            bad += 1
            for x in fails:
                print(f'FAIL {name}: {x}')
        else:
            print(f"OK   {name} ({kind}): {r.get('option')}={r.get('on')} exe {r.get('exe_sha256', '')[:16]}...")
    if a.json:
        with open(a.json, 'w', newline='\n') as f:
            json.dump(report, f, indent=1)
            f.write('\n')
    print(f'index_check: {len(report)} line(s), {bad} failed')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
