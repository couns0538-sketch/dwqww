from pathlib import Path
import re
import sys

from identity import EngineRun, check_logs


EXPECTED = (
    ('default', 'bench 11', 312866),
    ('default', 'bench 13', 862329),
    ('default', 'go perft 5', 4865609),
    ('PC20', 'bench 11', 278024),
    ('PC20', 'bench 13', 587276),
)


def main():
    executable, out = map(Path, sys.argv[1:])
    gate = True
    for profile, command, pin in EXPECTED:
        stem = f'{profile}_' + command.replace(' ', '_')
        out_path = out / f'{stem}.stdout.txt'
        err_path = out / f'{stem}.stderr.txt'
        cmd_path = out / f'{stem}.commands.txt'
        with (out_path.open('xb') as stdout, err_path.open('x+b') as stderr,
              cmd_path.open('xb') as commands, EngineRun(executable, stdout, stderr, commands, 60) as engine):
            if profile == 'PC20':
                engine.set_up(None)
            if command.startswith('bench '):
                depth = command.split()[1]
                label = re.compile(rb'^info string bench depth ' + depth.encode() + rb' nodes (\d+)\b')
            else:
                engine.send('position startpos')
                label = re.compile(rb'^nodes (\d+)$')
            engine.send(command)
            reply = engine.receive(label.match, f'{profile} {command}')
        check_logs(out_path, err_path)
        nodes = int(label.match(reply[-1])[1])
        gate &= nodes == pin
        print(f'{profile} {command}: observed {nodes} expected {pin}', flush=True)
    return 0 if gate else 1


if __name__ == '__main__':
    raise SystemExit(main())
