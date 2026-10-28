"""Measure prebench pins exactly like forge_queue.ps1 r7 Bench1 does (read-only on the exe).

Per depth, one fresh engine process gets, in this order:
  uci / setoption name Threads value 1 / setoption name Hash value 16 / setoption name OwnBook value false /
  setoption name <K> value <V> (each gate option, in order) / isready / bench <d> / quit
and the line 'bench depth D nodes N time T nps S' is parsed (the runner's regex).

Usage: python -I -B measure_pins.py <exe> <out.json> [--set LABEL=K1:V1,K2:V2 ...] [--depths 11,13,16,20,22]
  LABEL 'OFF' with no options is always measured first.
"""
import argparse
import json
import re
import subprocess
import time

RX = re.compile(r'bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)')


def bench1(exe, d, opts):
    lines = ['uci', 'setoption name Threads value 1', 'setoption name Hash value 16',
             'setoption name OwnBook value false']
    lines += [f'setoption name {k} value {v}' for k, v in opts]
    lines += ['isready', f'bench {d}', 'quit']
    t0 = time.time()
    p = subprocess.run([exe], input=('\n'.join(lines) + '\n').encode(), capture_output=True, timeout=3600)
    out = p.stdout.decode('latin-1')
    m = RX.search(out)
    info = [ln for ln in out.splitlines() if ln.startswith('info string')]
    errs = [ln for ln in out.splitlines() if 'ERROR' in ln]
    return {'depth': d, 'nodes': int(m.group(2)) if m else -1, 'time_ms': int(m.group(3)) if m else -1,
            'nps': int(m.group(4)) if m else -1, 'exit': p.returncode, 'wall_s': round(time.time() - t0, 1),
            'info_strings': info[:5], 'errors': errs[:5]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('out')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--depths', default='11,13,16,20,22')
    a = ap.parse_args()
    depths = [int(x) for x in a.depths.split(',')]
    sets = [('OFF', [])]
    for s in a.set:
        label, _, rest = s.partition('=')
        opts = []
        for kv in rest.split(','):
            if kv:
                k, _, v = kv.partition(':')
                opts.append((k, v))
        sets.append((label, opts))
    res = {'exe': a.exe, 'depths': depths, 'runs': {}}
    for label, opts in sets:
        rows = [bench1(a.exe, d, opts) for d in depths]
        res['runs'][label] = {'options': [f'option.{k}={v}' for k, v in opts], 'rows': rows,
                              'pins': [r['nodes'] for r in rows]}
        print(f'{label:24s} {" ".join("option.%s=%s" % kv for kv in opts):60s} '
              f'{"/".join(str(r["nodes"]) for r in rows)}  exit {[r["exit"] for r in rows]}', flush=True)
        with open(a.out, 'w', newline='\n') as fh:
            json.dump(res, fh, indent=1)


if __name__ == '__main__':
    main()
