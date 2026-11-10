#!/usr/bin/env python3
"""Sequential, fixed-depth T1 equivalence screen. Not a strength/speed test."""
import argparse
import hashlib
import json
import pathlib
import queue
import subprocess
import threading


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class Engine:
    def __init__(self, path, nnue):
        self.process = subprocess.Popen([str(path)], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, bufsize=1)
        self.lines = queue.Queue()
        def read():
            for line in self.process.stdout:
                self.lines.put(line.rstrip())
            self.lines.put(None)
        self.reader = threading.Thread(target=read, daemon=True)
        self.reader.start()
        self.send('uci')
        self.until('uciok')
        for option in ['Threads value 1', 'Hash value 16', 'OwnBook value false',
                       f'UseNNUE value {str(nnue).lower()}']:
            self.send('setoption name ' + option)
        self.send('isready')
        self.until('readyok')

    def send(self, text):
        self.process.stdin.write(text + '\n')
        self.process.stdin.flush()

    def until(self, prefix):
        output = []
        while True:
            line = self.lines.get(timeout=120)
            if line is None:
                raise RuntimeError('Engine exited: ' + repr(output[-5:]))
            output.append(line)
            if line == prefix or line.startswith(prefix + ' '):
                return output

    def search(self, fen, depth):
        self.send('ucinewgame')
        self.send('isready')
        self.until('readyok')
        self.send('position fen ' + fen)
        self.send('go depth ' + str(depth))
        lines = self.until('bestmove')
        infos = [line for line in lines if line.startswith('info depth ')]
        if not infos:
            raise RuntimeError('No depth info: ' + repr(lines))
        final = infos[-1].split()
        def value(name):
            return final[final.index(name) + 1]
        score_at = final.index('score')
        return {'depth': int(value('depth')), 'nodes': int(value('nodes')),
                'score': final[score_at + 1:score_at + 3],
                'pv': final[final.index('pv') + 1:],
                'bestmove': lines[-1].split()[1]}

    def close(self):
        if self.process.poll() is None:
            self.send('quit')
            self.process.wait(timeout=15)
        if self.process.returncode:
            raise RuntimeError(f'Engine exit {self.process.returncode}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('baseline', type=pathlib.Path)
    parser.add_argument('candidate', type=pathlib.Path)
    parser.add_argument('--fixtures', type=pathlib.Path,
                        default=pathlib.Path(__file__).with_name('equivalence_positions.fen'))
    parser.add_argument('--output', type=pathlib.Path,
                        default=pathlib.Path(__file__).with_name('equivalence_results.json'))
    parser.add_argument('--depth', type=int, default=7)
    args = parser.parse_args()
    positions = args.fixtures.read_text().splitlines()
    if len(positions) != 128 or len(set(positions)) != 128:
        raise RuntimeError('Expected 128 unique FENs')
    report = {'schema': 1, 'depth': args.depth, 'threads': 1, 'hash_mb': 16,
              'own_book': False, 'reset': 'ucinewgame + isready before every FEN',
              'fixture_sha256': sha(args.fixtures), 'position_count': len(positions),
              'binaries': {name: {'path': str(path.resolve()), 'sha256': sha(path)}
                           for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]},
              'runs': [], 'failures': []}
    for nnue in [True, False]:
        sets = {}
        for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]:
            engine = Engine(path.resolve(), nnue)
            records = []
            try:
                for i, fen in enumerate(positions):
                    result = engine.search(fen, args.depth)
                    records.append({'position': i, 'fen': fen, **result})
                    if (i + 1) % 32 == 0:
                        print(f'{name} NNUE={nnue}: {i + 1}/128', flush=True)
            finally:
                engine.close()
            report['runs'].append({'binary': name, 'nnue': nnue, 'results': records})
            sets[name] = records
            args.output.write_text(json.dumps(report, separators=(',', ':')) + '\n')
        for a, b in zip(sets['baseline'], sets['candidate']):
            if a != b:
                report['failures'].append({'nnue': nnue, 'baseline': a, 'candidate': b})
        args.output.write_text(json.dumps(report, separators=(',', ':')) + '\n')
    for name, binary in report['binaries'].items():
        if sha(binary['path']) != binary['sha256']:
            report['failures'].append({'error': 'binary changed during screen', 'binary': name})
    report['comparisons'] = len(positions) * 2
    report['passed'] = not report['failures']
    args.output.write_text(json.dumps(report, separators=(',', ':')) + '\n')
    print(f"Comparisons={report['comparisons']} failures={len(report['failures'])}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
