from pathlib import Path
import re
import sys

from identity import EngineRun, OPTION, PC20, check_logs

binary = Path(sys.argv[1]).resolve(strict=True)
output = Path(sys.argv[2])
base = {key: PC20[key] for key in ('Threads', 'Hash', 'MultiPV', 'UseNNUE', 'OwnBook')}
s14 = dict(list(PC20.items())[:19])
assert s14['NonPawnCorrection'] == 'true' and len(s14) - len(base) == 14
checks = [
    ('default', base, '11', 312866, True),
    ('default', base, '13', 862329, True),
    ('default', base, 'perft5', 4865609, True),
    ('default', base, '16', 3024920, False),
    ('S14', s14, '11', 242796, False),
    ('S14', s14, '13', 656517, False),
    ('PC20', PC20, '11', 278024, False),
    ('PC20', PC20, '13', 587276, False),
]
for profile, options, command, target, required in checks:
    prefix = output / f'pin_{profile}_{command}'
    out, err, sent = [Path(f'{prefix}{ext}') for ext in ('.txt', '.stderr.txt', '.commands.txt')]
    with out.open('xb') as stdout, err.open('xb') as stderr, sent.open('xb') as commands:
        with EngineRun(binary, stdout, stderr, commands, 30) as engine:
            engine.send('uci')
            hello = engine.receive(lambda row: row == b'uciok', 'uciok')
            advertised = {match[1].decode('ascii') for line in hello if (match := OPTION.match(line))}
            if missing := options.keys() - advertised:
                raise RuntimeError(f'missing required UCI settings: {sorted(missing)}')
            for key, value in options.items():
                engine.send(f'setoption name {key} value {value}')
            engine.ready()
            if command == 'perft5':
                engine.send('position startpos')
                engine.send('go perft 5')
                pattern = re.compile(rb'^nodes (\d+)$')
            else:
                engine.send(f'bench {command}')
                pattern = re.compile(rb'^info string bench depth ' + command.encode('ascii') + rb' nodes (\d+)\b')
            result = engine.receive(lambda row: pattern.match(row), command)[-1]
            nodes = int(pattern.match(result)[1])
    check_logs(out, err)
    if nodes == target:
        status = 'PASS'
    elif required:
        status = 'STOP'
    else:
        status = 'F1'
    print(profile, command, target, nodes, status, sep='\t', flush=True)
    if status == 'STOP':
        sys.exit(3)
