#!/usr/bin/env python3
"""selfplay_smoke.py - R13 sanitizer self-play smoke (CI, Linux ASan+UBSan build). Standard library only.

usage: python3 selfplay_smoke.py ENGINE --config NAME "N1=V1;N2=V2" [--config ...] [--games 4] [--nodes 20000]
         [--max-plies 160] [--threads 1] [--out summary.json]

Per config: one engine process (stderr captured to <out>.<config>.stderr), `games` games of self-play from fixed starts
(startpos + 3 bench positions), `go nodes N` per move, OwnBook false. Every bestmove is checked against the engine's own
`go perft 1` list (legal-move census). A game ends at mate/stalemate (empty list) or max plies. The run fails on an
illegal or missing bestmove, an engine exit, or any sanitizer line in stderr ("ERROR: AddressSanitizer",
"ERROR: LeakSanitizer", "runtime error:", "SUMMARY: "). Exit 0 = PASS.
"""
import argparse
import json
import re
import subprocess
import sys
import threading

STARTS = ['startpos',
          'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
          'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
          'fen r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 9']
SAN_RX = re.compile(r'ERROR: AddressSanitizer|ERROR: LeakSanitizer|runtime error:|SUMMARY: (Address|Undefined|Leak)')


def play(engine, name, line, games, nodes, max_plies, threads, out):
    err_path = f'{out}.{name}.stderr'
    errf = open(err_path, 'w')
    p = subprocess.Popen([engine], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errf, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + '\n')
        p.stdin.flush()

    def wait(rx, keep=None):
        r = re.compile(rx)
        kept = []
        for ln in p.stdout:
            if keep and re.match(keep, ln):
                kept.append(ln.strip())
            m = r.search(ln)
            if m:
                return m, kept
        raise RuntimeError('engine exited before ' + rx)

    stats = {'config': name, 'line': line, 'games': 0, 'moves': 0, 'illegal': 0, 'results': [], 'error': None}
    try:
        send('uci')
        wait(r'^uciok')
        send('setoption name OwnBook value false')
        send(f'setoption name Threads value {threads}')
        send('setoption name Hash value 16')
        for kv in [x for x in line.split(';') if x]:
            n, v = kv.split('=', 1)
            send(f'setoption name {n} value {v}')
        for g in range(games):
            start = STARTS[g % len(STARTS)]
            moves = []
            send('ucinewgame')
            send('isready')
            wait(r'^readyok')
            result = 'maxplies'
            for _ in range(max_plies):
                pos = start + (' moves ' + ' '.join(moves) if moves else '')
                send('position ' + pos)
                send('go perft 1')
                _, kept = wait(r'^nodes \d+', keep=r'^[a-h][1-8][a-h][1-8][qrbn]?: \d+')
                legal = {k.split(':')[0] for k in kept}
                if not legal:
                    result = 'mate_or_stalemate'
                    break
                send(f'go nodes {nodes}')
                m, _ = wait(r'^bestmove (\S+)')
                best = m.group(1)
                if best not in legal:
                    stats['illegal'] += 1
                    result = f'illegal {best}'
                    break
                moves.append(best)
                stats['moves'] += 1
            stats['games'] += 1
            stats['results'].append(result)
        send('quit')
        p.wait(timeout=120)
    except Exception as exc:  # engine crash (sanitizer abort) or protocol error
        stats['error'] = repr(exc)
        try:
            p.kill()
        except Exception:
            pass
    errf.close()
    san = [ln.rstrip() for ln in open(err_path, errors='replace') if SAN_RX.search(ln)]
    stats['sanitizer_lines'] = len(san)
    stats['sanitizer_first'] = san[:5]
    stats['exit_code'] = p.returncode
    stats['pass'] = stats['illegal'] == 0 and not san and stats['error'] is None and p.returncode == 0
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('engine')
    ap.add_argument('--config', nargs=2, action='append', metavar=('NAME', 'LINE'), required=True)
    ap.add_argument('--games', type=int, default=4)
    ap.add_argument('--nodes', type=int, default=20000)
    ap.add_argument('--max-plies', type=int, default=160)
    ap.add_argument('--threads', type=int, default=1)
    ap.add_argument('--out', default='selfplay_smoke')
    a = ap.parse_args()
    results = []
    lock = threading.Lock()
    for name, line in a.config:
        s = play(a.engine, name, line, a.games, a.nodes, a.max_plies, a.threads, a.out)
        with lock:
            results.append(s)
        print(json.dumps({k: s[k] for k in ('config', 'line', 'games', 'moves', 'illegal', 'sanitizer_lines',
                                             'exit_code', 'error', 'pass')}), flush=True)
    ok = all(s['pass'] for s in results)
    with open(a.out + '.json', 'w') as fh:
        json.dump({'pass': ok, 'configs': results}, fh, indent=1)
    print('SELFPLAY SMOKE ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
