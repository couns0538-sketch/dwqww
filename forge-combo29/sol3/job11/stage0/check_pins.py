from pathlib import Path
import re
import subprocess
import sys

from identity import EngineRun

stage, net, k13, k14 = map(Path, sys.argv[1:])
expected = {'default': (312866, 862329, 4865609), 'PC20_net768': (882074, 4275906)}
for mode, wanted in expected.items():
    for arm, executable in [('k13', k13), ('k14', k14)]:
        stem = stage / f'{arm}_{mode}'
        if mode == 'default':
            commands = 'bench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n'
            stem.with_suffix('.commands.txt').write_text(commands, encoding='ascii')
            with stem.with_suffix('.stdout.txt').open('xb') as out, stem.with_suffix('.stderr.txt').open('xb') as err:
                subprocess.run([executable], input=commands.encode('ascii'), stdout=out, stderr=err,
                               check=True, timeout=60)
        else:
            files = [stem.with_suffix(ext) for ext in ('.stdout.txt', '.stderr.txt', '.commands.txt')]
            with files[0].open('xb') as out, files[1].open('x+b') as err, files[2].open('xb') as commands:
                with EngineRun(executable, out, err, commands, 60) as engine:
                    engine.set_up(net)
                    for depth in (11, 13):
                        engine.send(f'bench {depth}')
                        engine.receive(lambda line: line.startswith(f'info string bench depth {depth} nodes '.encode()),
                                       f'bench {depth} summary')
        raw = stem.with_suffix('.stdout.txt').read_text(encoding='ascii')
        found = re.findall(r'^info string bench depth (11|13) nodes (\d+) ', raw, re.M)
        if [depth for depth, _ in found] != ['11', '13']:
            raise ValueError(f'{arm}/{mode}: invalid bench output {found}')
        counts = tuple(int(nodes) for _, nodes in found)
        if mode == 'default':
            perft = re.findall(r'^nodes (\d+)$', raw, re.M)
            if len(perft) != 1:
                raise ValueError(f'{arm}/{mode}: invalid perft output {perft}')
            counts += (int(perft[0]),)
        print(arm, mode, *counts, flush=True)
        if counts != wanted:
            raise ValueError(f'{arm}/{mode}: expected {wanted}, received {counts}')
