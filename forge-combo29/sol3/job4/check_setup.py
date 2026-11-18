from pathlib import Path
import re
import sys

from identity import EngineRun, check_logs, run_benches

exe = Path(sys.argv[1]).resolve(strict=True)
base = Path(sys.argv[2])
log, errors, commands = [Path(f'{base}{ending}') for ending in ('.txt','.stderr.txt','.commands.txt')]
with log.open('xb') as stdout, errors.open('xb') as stderr, commands.open('xb') as stdin:
    if len(sys.argv) == 3:
        counts = run_benches(exe, (stdout, stderr, stdin), 30)
        if counts != {11: 278024, 13: 587276}:
            raise RuntimeError(f'k11 bench known-answer mismatch: {counts}')
        print('k11 PC20 bench 11/13: 278024/587276')
    else:
        net = Path(sys.argv[3]).resolve(strict=True)
        with EngineRun(exe, stdout, stderr, stdin, 30) as engine:
            engine.set_up()
            engine.send(f'setoption name NNUEArchFile value {net}')
            engine.send('setoption name NNUEArch value true')
            engine.send('isready')
            reply = engine.receive(lambda line: line == b'readyok', 'NNUE readyok')
            active = [line for line in reply if line.startswith(b'info string NNUE v3 active:')]
            if len(active) != 1 or not re.search(rb'\bchecksum 30ab43b4ba5db5f3\b', active[0]):
                raise RuntimeError(f'bad NNUE active evidence: {reply!r}')
            print(active[0].decode('ascii'))
check_logs(log, errors)
