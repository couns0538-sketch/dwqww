import argparse
from pathlib import Path
import re

from identity import EngineRun, check_logs


DEFAULT = (('bench 11', 312866), ('bench 13', 862329), ('go perft 5', 4865609))
NET768 = (('bench 11', 882074), ('bench 13', 4275906))
ACTIVE = re.compile(rb'^info string NNUE v3 active: .*\bhidden 768\b.*\bchecksum 30ab43b4ba5db5f3\b')


def run_pin(executable, output, name, command, expected, net):
    stem = f'{name}_' + command.replace(' ', '_')
    out_path = output / f'{stem}.stdout.txt'
    err_path = output / f'{stem}.stderr.txt'
    cmd_path = output / f'{stem}.commands.txt'
    with (out_path.open('xb') as stdout, err_path.open('x+b') as stderr,
          cmd_path.open('xb') as commands, EngineRun(executable, stdout, stderr, commands, 60) as engine):
        if net is not None:
            engine.set_up(net)
        if command.startswith('bench '):
            depth = command.split()[1]
            label = re.compile(rb'^info string bench depth ' + depth.encode() + rb' nodes (\d+)\b')
        else:
            engine.send('position startpos')
            label = re.compile(rb'^nodes (\d+)$')
        engine.send(command)
        response = engine.receive(label.match, f'{name} {command}')
    check_logs(out_path, err_path)
    if net is not None:
        active = [line for line in out_path.read_bytes().splitlines() if ACTIVE.search(line)]
        if len(active) != 1:
            raise ValueError(f'{stem} requires one checksum-matching activation, got {active!r}')
        print(active[0].decode('ascii'), flush=True)
    nodes = int(label.match(response[-1])[1])
    print(f'{name} {command}: observed {nodes} expected {expected}', flush=True)
    return nodes == expected


def main():
    parser = argparse.ArgumentParser(description='Run independent fresh-process Job19 pins.')
    parser.add_argument('executable', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('net', type=Path)
    parser.add_argument('--net-only', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    if not args.net_only:
        results.extend(run_pin(args.executable, args.output, 'default', command, pin, None)
                       for command, pin in DEFAULT)
    results.extend(run_pin(args.executable, args.output, 'PC20_net768', command, pin, args.net)
                   for command, pin in NET768)
    return 0 if all(results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
