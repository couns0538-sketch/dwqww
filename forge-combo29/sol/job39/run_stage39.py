"""Run Job 39 controls or one complete tuning-draw group."""

from concurrent.futures import ThreadPoolExecutor
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parent
CONTROL = {
    'K39': (('K39a', '1', False), ('K39b', '1', False)),
    'C39': (('C39', '1', True),),
    'L39': (('L39', 'pc20', False),),
}


def run(build, draw, first, mode, output, deadline, lmr60=False):
    if time.time() >= deadline:
        return 130, 'not played'
    command = [
        sys.executable, '-u', str(ROOT / 'run_draw39.py'),
        '--build', build, '--draw', str(draw), '--first', str(first), '--last', str(first + 9),
        '--mode', mode, '--output', str(output), '--deadline', str(deadline),
    ]
    if lmr60:
        command.append('--lmr60')
    path = output.relative_to(ROOT / 'raw')
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), path, 'start', flush=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.parent / f'{output.name}.driver.out'
    with log.open('x', encoding='utf-8') as stream:
        process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, cwd=ROOT, check=False)
    receipt = output / 'run.json'
    status = json.loads(receipt.read_text())['status'] if receipt.is_file() else 'unfinalized'
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), path, status, process.returncode, flush=True)
    return process.returncode, status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=(*CONTROL, 'A', 'B'))
    parser.add_argument('--deadline', type=int, required=True)
    parser.add_argument('--workers', type=int, required=True)
    args = parser.parse_args()
    raw = ROOT / 'raw'
    raw.mkdir(exist_ok=True)
    if args.stage in CONTROL:
        for label, draw, lmr60 in CONTROL[args.stage]:
            code, _status = run('r15d', draw, 390001, 'hard', raw / label, args.deadline, lmr60)
            if code:
                return code
        return 0

    mode, base = ('hard', 391000) if args.stage == 'A' else ('soft', 392000)

    def paired(draw):
        folder = raw / args.stage / f'draw-{draw:03d}'
        first = base + 10 * draw
        _code, status = run('r15d', draw, first, mode, folder / 'r15d', args.deadline)
        if status != 'refused':
            run('kF', draw, first, mode, folder / 'kF', args.deadline)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for _ in pool.map(paired, range(1, 101)):
            pass
    return 130 if time.time() >= args.deadline else 0


if __name__ == '__main__':
    sys.exit(main())
