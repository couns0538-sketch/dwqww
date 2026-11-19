"""Run the Job 40 gate or the one-option cells for one node limit."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
CONTROLS = (
    ('BASE-a', None, None),
    ('BASE-b', None, None),
    ('EvalSwingMax220', 'EvalSwingMax', 220),
    ('CaptureFutilityMultiplier275', 'CaptureFutilityMultiplier', 275),
    ('LmrQuietBase/PLUS', 'LmrQuietBase', 101),
)


def words():
    with (ROOT / 'design40.tsv').open(encoding='utf-8') as source:
        for setting in csv.DictReader(source, delimiter='\t'):
            name = setting['name']
            yield f'{name}/{setting["minus_variant"]}', name, int(setting['minus'])
            if name != 'LmrQuietBase':
                yield f'{name}/PLUS', name, int(setting['plus'])


def launch(args, spec):
    if time.time() >= args.deadline:
        return 130, 'not played'
    label, name, value = spec
    raw = ROOT / 'raw' / args.limit
    output = raw / label
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable, '-u', str(ROOT / 'run_cell40.py'), args.limit,
        '--output', str(output), '--deadline', str(args.deadline),
    ]
    if name is not None:
        command.extend(('--option', name, str(value)))
    label = str(output.relative_to(ROOT / 'raw'))
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), label, 'start', flush=True)
    log = output.parent / f'{output.name}.driver.out'
    with log.open('x', encoding='utf-8') as stream:
        proc = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=False)
    receipt = output / 'run.json'
    status = json.loads(receipt.read_text())['status'] if receipt.is_file() else 'unfinalized'
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), label, status, proc.returncode, flush=True)
    return proc.returncode, status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('limit', choices=('N2', 'N1'))
    parser.add_argument('part', choices=('gate', 'settings'))
    parser.add_argument('--deadline', type=int, required=True)
    parser.add_argument('--workers', type=int, required=True)
    args = parser.parse_args()
    if args.part == 'gate':
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            outcomes = list(pool.map(lambda spec: launch(args, spec), CONTROLS))
        return next((code for code, _ in outcomes if code), 0)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for _ in pool.map(lambda cell: launch(args, cell), words()):
            pass
    return 130 if time.time() >= args.deadline else 0


if __name__ == '__main__':
    sys.exit(main())
