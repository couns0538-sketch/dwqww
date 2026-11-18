import argparse
import json
from pathlib import Path
import re

from identity import EngineRun
from pins19 import ACTIVE


EXPECTED = {11: 882074, 13: 4275906}


def main():
    parser = argparse.ArgumentParser(description='Run one fresh-process AU benchmark pin.')
    parser.add_argument('executable', type=Path)
    parser.add_argument('net', type=Path)
    parser.add_argument('depth', type=int, choices=EXPECTED)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [args.output / f'engine.{name}.txt' for name in ('stdout', 'stderr', 'commands')]
    label = re.compile(rb'^info string bench depth ' + str(args.depth).encode() + rb' nodes (\d+)\b')
    status, error, nodes = None, None, None
    with (paths[0].open('xb') as stdout, paths[1].open('x+b') as stderr, paths[2].open('xb') as commands):
        engine = EngineRun(args.executable, stdout, stderr, commands, 300)
        try:
            with engine:
                engine.set_up(args.net)
                engine.send(f'bench {args.depth}')
                response = engine.receive(label.match, f'bench {args.depth}')
            nodes = int(label.match(response[-1])[1])
        except (OSError, ValueError, RuntimeError) as failure:
            error = str(failure)
        if hasattr(engine, 'process'):
            status = engine.process.returncode
    output = paths[0].read_bytes().splitlines()
    active = [line.decode('ascii') for line in output if ACTIVE.search(line)]
    result = {'build': str(args.executable), 'depth': args.depth, 'observed_nodes': nodes,
              'expected_nodes': EXPECTED[args.depth], 'engine_exit': status, 'error': error,
              'net_active': active, 'matches_known': nodes == EXPECTED[args.depth] and status == 0 and len(active) == 1}
    receipt = json.dumps(result, indent=2) + '\n'
    (args.output / 'summary.json').write_text(receipt)
    print(receipt, end='')
    return int(not result['matches_known'])


if __name__ == '__main__':
    raise SystemExit(main())
