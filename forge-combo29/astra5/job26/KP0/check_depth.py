"""Run one built-in, NodeClock-default, PC20 depth-12 suite with complete protocol evidence."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import csv

SUITES = {
    'O': ('02d59eaf2515a4e11aecb78c5736db193812516f42ab8a6aa0b2411332186300', 200, 8315168),
    'G': ('af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d', 353, 17611204),
}
ENGINE_SHA = '9f95f854dd0dd6dd5c201a8303cc52dfbbcc74e4796b0b6850e216ab756b68e3'
SETTINGS_SHA = '2c4785517c8eb7a47ac39d282bc3917f77a5d0264c18b7898036e4abbefe6d5f'

def run(args):
    digest, count, reference = SUITES[args.suite]
    nc, epd = args.exe.resolve(), args.input_dir / (args.suite + '.epd')
    for path, expected in [(nc, ENGINE_SHA), (epd, digest), (args.pc20, SETTINGS_SHA)]:
        if sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'identity mismatch for {path}')
    dest = args.out / args.suite
    dest.mkdir(parents=True, exist_ok=False)
    fens = [' '.join(line.split()[:4]) + ' 0 1' for line in epd.read_text().splitlines()]
    if len(fens) != count:
        raise ValueError('EPD count mismatch')
    options = args.pc20.read_text().splitlines()
    begin = datetime.now(timezone.utc).isoformat()
    with (dest / 'uci.log').open('x') as log, (dest / 'rows.tsv').open('x',newline='') as rows, \
         subprocess.Popen([nc], cwd=nc.parent, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, bufsize=1) as engine:
        writer = csv.writer(rows, delimiter='\t',lineterminator='\n')
        writer.writerow(('position','fen','last_depth','depth_nodes','final_nodes','bestmove'))
        nfooter = nchanged = total = 0
        def send(command):
            print('> ' + command, file=log)
            engine.stdin.write(command + '\n')
            engine.stdin.flush()
        def read():
            line = engine.stdout.readline()
            if not line:
                raise RuntimeError('unexpected EOF')
            line = line.rstrip('\r\n')
            print('< ' + line, file=log)
            if any(word in line.lower() for word in ('unknown option','invalid value','error','nnue v3 loaded','nnue v3 active')):
                raise RuntimeError(line)
            return line
        try:
            send('uci')
            names = set()
            while (line := read()) != 'uciok':
                if match := re.match(r'option name (.+?) type ', line):
                    names.add(match[1])
            for option in options:
                if option.split(' value ')[0].removeprefix('setoption name ') not in names:
                    raise ValueError(f'option missing: {option}')
                send(option)
            for i, fen in enumerate(fens, 1):
                send('ucinewgame')
                send('isready')
                while read() != 'readyok':
                    pass
                send('position fen ' + fen)
                send('go depth 12')
                depth = depth_nodes = last_info = None
                footers = []
                while not (line := read()).startswith('bestmove '):
                    if line.startswith('info '):
                        last_info = line
                    if line.startswith('info depth ') and ' nodes ' in line:
                        fields = line.split()
                        depth = int(fields[2])
                        depth_nodes = int(fields[fields.index('nodes') + 1])
                    if m := re.fullmatch(r'info string softnodes nodes (\d+)', line):
                        footers.append(int(m[1]))
                m = re.search(r'\bnodes (\d+)\b',last_info or '')
                if not m or not depth or len(footers) > 1:
                    raise ValueError(f'position {i} has unexpected last info {last_info!r} or footers {footers!r}')
                actual = int(m[1])
                if footers and actual != footers[0]:
                    raise ValueError(f'footer is superseded at position {i}')
                total += actual
                nfooter += bool(footers)
                nchanged += actual != depth_nodes
                writer.writerow((i, fen, depth, depth_nodes, actual, line.split()[1]))
            send('quit')
            engine.stdin.close()
            if engine.wait(timeout=10):
                raise RuntimeError('engine quit failed')
        finally:
            if engine.poll() is None:
                engine.kill()
    summary = (f'suite {args.suite}\nstart_utc {begin}\nend_utc {datetime.now(timezone.utc).isoformat()}\n'
               f'executable {nc}\nengine_sha256 {ENGINE_SHA}\nepd_sha256 {digest}\n'
               f'positions {count}\nfinal footers {nfooter}\nlast info vs last depth node differences {nchanged}\n'
               f'expected {reference}\nsum of literal last info nodes {total}\n'
               f'{"PASS" if total == reference else "FAIL"}\n')
    (dest / 'comparison.txt').write_text(summary)
    print(summary,end='')
    if total != reference:
        raise ValueError(f'{args.suite} sum mismatch')

if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('suite',choices=SUITES)
    for key in ('exe','input_dir','pc20','out'):
        cli.add_argument(key,type=Path)
    run(cli.parse_args())
