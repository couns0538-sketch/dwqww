from pathlib import Path
import re
import subprocess
import sys

from identity import EngineRun

out, executable, net = map(Path, sys.argv[1:])
default = 'bench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n'
(out / 'default.commands.txt').write_text(default, encoding='ascii')
with (out / 'default.stdout.txt').open('xb') as stdout, (out / 'default.stderr.txt').open('xb') as stderr:
    subprocess.run([executable], input=default.encode('ascii'), stdout=stdout, stderr=stderr, check=True, timeout=60)

def bench(path):
    raw = path.read_text(encoding='ascii')
    return tuple((int(depth), int(nodes)) for depth, nodes in re.findall(r'^info string bench depth (11|13) nodes (\d+) ', raw, re.M))

default_target = ((11, 312866), (13, 862329))
raw = (out / 'default.stdout.txt').read_text(encoding='ascii')
bare = bench(out / 'default.stdout.txt')
perft = re.findall(r'^nodes (\d+)$', raw, re.M)
print('default', bare, perft, flush=True)
if bare != default_target or perft != ['4865609']:
    raise ValueError('Default gates failed')
for name, evaluator, expected in [('pc20_builtin', None, ((11, 278024), (13, 587276)))]: 
    with ((out / f'{name}.stdout.txt').open('xb') as stdout,
          (out / f'{name}.stderr.txt').open('x+b') as stderr,
          (out / f'{name}.commands.txt').open('xb') as commands):
        with EngineRun(executable, stdout, stderr, commands, 60) as engine:
            engine.set_up(evaluator)
            for depth in (11, 13):
                engine.send(f'bench {depth}')
                engine.receive(lambda line: line.startswith(f'info string bench depth {depth} nodes '.encode()),
                               f'bench depth {depth}')
    actual = bench(out / f'{name}.stdout.txt')
    if tuple(depth for depth, _ in actual) != (11, 13):
        raise ValueError(f'{name}: malformed benchmark results')
    print(name, actual, 'reference', expected, 'equal', actual == expected)
