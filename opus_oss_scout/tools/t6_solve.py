#!/usr/bin/env python3
"""t6_solve.py - OSS scout T6: Lichess puzzle solve rate of a UCI engine at a fixed node budget (a fast tactical screen).

usage: python -I -B t6_solve.py <engine.exe> <puzzles.jsonl> --nodes 20000 [--nodes 200000 ...] [--out result.json]
Per puzzle (Lichess format: FEN before the opponent's move, Moves = opponent move, solution, ...): ucinewgame,
`position fen <FEN> moves <m0>`, `go nodes N`, and compare bestmove with m1 (the first solution move). Fixed nodes with
Threads 1 make each answer independent of CPU load. Prints the solve rate overall, per rating band and for mate
themes. Options sent: OwnBook false, Hash 16, Threads 1. Stdlib only.
"""
import json
import subprocess
import sys
import time

BANDS = [(0, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 4000)]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, bufsize=1)
        self.send('uci')
        self.wait('uciok')
        for opt in ('OwnBook value false', 'Hash value 16', 'Threads value 1'):
            self.send('setoption name ' + opt)
        self.send('isready')
        self.wait('readyok')

    def send(self, s):
        self.p.stdin.write(s + '\n')
        self.p.stdin.flush()

    def wait(self, token):
        lines = []
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError('engine closed its output')
            line = line.strip()
            lines.append(line)
            if line.startswith(token):
                return lines

    def best(self, fen, first, nodes):
        self.send('ucinewgame')
        self.send('isready')
        self.wait('readyok')
        self.send(f'position fen {fen} moves {first}')
        self.send(f'go nodes {nodes}')
        lines = self.wait('bestmove')
        bm = lines[-1].split()[1] if len(lines[-1].split()) > 1 else ''
        score = ''
        for l in reversed(lines):
            if ' score ' in l:
                t = l.split()
                i = t.index('score')
                score = ' '.join(t[i + 1:i + 3])
                break
        return bm, score

    def close(self):
        try:
            self.send('quit')
            self.p.wait(timeout=10)
        except Exception:
            pass


def main(argv):
    exe, pz = argv[0], argv[1]
    nodes_list, out = [], None
    i = 2
    while i < len(argv):
        if argv[i] == '--nodes':
            nodes_list.append(int(argv[i + 1]))
        elif argv[i] == '--out':
            out = argv[i + 1]
        i += 2
    puzzles = [json.loads(l) for l in open(pz, encoding='utf-8')]
    eng = Engine(exe)
    report = {'engine': exe, 'puzzles': len(puzzles), 'runs': []}
    for nodes in nodes_list:
        t0 = time.time()
        solved = 0
        band_tot = [0] * len(BANDS)
        band_ok = [0] * len(BANDS)
        mate_tot = mate_ok = 0
        fails = []
        for p in puzzles:
            mv = p['Moves'].split()
            bm, score = eng.best(p['FEN'], mv[0], nodes)
            ok = bm == mv[1]
            solved += ok
            b = next(k for k, (lo, hi) in enumerate(BANDS) if lo <= p['Rating'] < hi)
            band_tot[b] += 1
            band_ok[b] += ok
            if any(t.startswith('mate') for t in (p.get('Themes') or [])):
                mate_tot += 1
                mate_ok += ok
            if not ok and len(fails) < 30:
                fails.append({'id': p['PuzzleId'], 'rating': p['Rating'], 'want': mv[1], 'got': bm, 'score': score})
        sec = time.time() - t0
        run = {'nodes': nodes, 'solved': solved, 'rate': solved / len(puzzles), 'seconds': round(sec, 1),
               'bands': [{'band': f'{lo}-{hi - 1}', 'n': band_tot[k], 'solved': band_ok[k],
                          'rate': (band_ok[k] / band_tot[k]) if band_tot[k] else None} for k, (lo, hi) in enumerate(BANDS)],
               'mate_themes': {'n': mate_tot, 'solved': mate_ok, 'rate': mate_ok / mate_tot if mate_tot else None},
               'first_failures': fails}
        report['runs'].append(run)
        print(f'nodes {nodes}: solved {solved}/{len(puzzles)} = {100.0 * solved / len(puzzles):.1f} % in {sec:.0f} s')
        for bd in run['bands']:
            if bd['n']:
                print(f"   rating {bd['band']:>9}: {bd['solved']:4d}/{bd['n']:4d} = {100.0 * bd['rate']:.1f} %")
        print(f"   mate themes: {mate_ok}/{mate_tot}")
    eng.close()
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(report, f, indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
