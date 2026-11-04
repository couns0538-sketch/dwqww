#!/usr/bin/env python3
"""test_spsa_sim.py [--cpus 1] - Opus 30-h job: end-to-end SPSA simulation test of tune_spsa.py (own code).
The real tuner drives a FAKE fastchess (sim/fake_fastchess.bat -> fake_fastchess.py) whose games follow a strength
model with a known optimum (A = 160, scale 40; B = 20, scale 10; Elo = -60 * sum(((v - opt) / scale)^2)). Starting at
A = 100, B = 60, a correct tuner must move both toward the optimum: the sign of W - L, the plus / minus option values on
the command line, the PGN parsing, the schedule and the clamping are all on the path. Then a resume must continue the
same run (k and batch continue, history rows = records). PASS = both distances to the optimum at least halved after
1,000 pairs, and the resume checks hold. Runs in a new folder under D:\\o30\\tmp; busy check off (max_busy_percent 100).
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(HERE)
PY = r'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cpus', default='1')
    a = ap.parse_args()
    work = r'D:\o30\tmp\spsa_sim_' + time.strftime('%H%M%S')
    os.makedirs(work)
    params = os.path.join(work, 'params.csv')
    with open(params, 'x', newline='\n') as f:
        f.write('name,start,min,max,c,a\nA,100,0,300,20,0.05\nB,60,0,200,8,0.05\n')
    cfg = {'name': 'SPSA simulation test (fake fastchess, known optimum A=160 B=20)', 'engine': 'not-used.exe',
           'fastchess': os.path.join(HERE, 'fake_fastchess.bat'),
           'book': r'C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd', 'book_format': 'epd',
           'book_openings': 1000, 'tc': '1+0.01', 'hash': 16, 'pairs_planned': 1000, 'pairs_per_batch': 10,
           'alpha': 0.602, 'gamma': 0.101, 'A_ratio': 0.1, 'seed': 7, 'threads': 1, 'cpus': a.cpus,
           'params_csv': params, 'fixed_options': {}, 'max_busy_percent': 100.0}
    cfgp = os.path.join(work, 'config.json')
    with open(cfgp, 'x', newline='\n') as f:
        json.dump(cfg, f, indent=1)
    run = os.path.join(work, 'run')
    env = dict(os.environ, SIM_OPT='{"A": [160, 40], "B": [20, 10]}', SIM_K='60')
    tuner = os.path.join(B, 'tune_spsa.py')
    r1 = subprocess.run([PY, '-I', '-B', tuner, 'run', cfgp, run, '--max-pairs', '1000'], env=env,
                        capture_output=True, text=True, timeout=3600)
    hist = list(csv.DictReader(open(os.path.join(run, 'history.csv'))))
    first, last = hist[0], hist[-1]
    dA0, dB0 = abs(100 - 160), abs(60 - 20)
    dA, dB = abs(float(last['A']) - 160), abs(float(last['B']) - 20)
    print(f'session 1: exit {r1.returncode}, {len(hist) - 1} batches, pairs {last["pairs_total"]}, '
          f'A {first["A"]} -> {last["A"]} (optimum 160), B {first["B"]} -> {last["B"]} (optimum 20)')
    ok1 = r1.returncode == 0 and int(last['pairs_total']) == 1000 and dA <= dA0 / 2 and dB <= dB0 / 2
    r2 = subprocess.run([PY, '-I', '-B', tuner, 'run', cfgp, run, '--resume', '--max-pairs', '200'], env=env,
                        capture_output=True, text=True, timeout=3600)
    hist2 = list(csv.DictReader(open(os.path.join(run, 'history.csv'))))
    recs = [json.loads(l) for l in open(os.path.join(run, 'iterations.jsonl')) if l.startswith('{')]
    ks = [(r['k_before'], r['k_after']) for r in recs]
    contiguous = all(ks[i][1] == ks[i + 1][0] for i in range(len(ks) - 1)) and ks[0][0] == 0
    batches = [r['batch'] for r in recs] == list(range(len(recs)))
    ok2 = (r2.returncode == 0 and int(hist2[-1]['pairs_total']) == 1200 and len(hist2) - 1 == len(recs)
           and contiguous and batches)
    print(f'session 2 (resume): exit {r2.returncode}, pairs {hist2[-1]["pairs_total"]}, records {len(recs)} = history rows '
          f'{len(hist2) - 1}: {len(hist2) - 1 == len(recs)}, k contiguous {contiguous}, batch numbers {batches}, '
          f'A {hist2[-1]["A"]}, B {hist2[-1]["B"]}')
    if not (ok1 and ok2):
        print(r1.stdout[-1500:], r1.stderr[-1500:], r2.stdout[-800:], r2.stderr[-800:])
    print(f"SPSA SIM {'PASS' if ok1 and ok2 else 'FAIL'}: distance to the optimum A {dA0} -> {dA:.1f}, B {dB0} -> {dB:.1f} "
          f"after 1,000 pairs (must at least halve); resume {'ok' if ok2 else 'FAILED'} (folder {work})")
    sys.exit(0 if ok1 and ok2 else 1)


if __name__ == '__main__':
    main()
