#!/usr/bin/env python3
"""cand_checks.py - R13 per-candidate UCI checks (run under run_low.ps1: BelowNormal, 2-CPU mask, children inherit).

usage: python -I -B cand_checks.py EXE OUT.json --line "N1=V1;N2=V2" [--line ...] [--new-opt NAME ...]
         [--mate-epd FILE] [--mate-nodes 3000000] [--movetime 1000]

1. uci: every --new-opt is advertised and its default is OFF (0 / false / an "off"-like string).
2. T1 / T4 movetime smoke per --line (and OFF): ucinewgame, OwnBook false, Threads 1 and 4, `go movetime`, waits for
   bestmove (never sends quit early), then checks the bestmove is in the engine's own `go perft 1` list.
3. mate probe: every EPD position, OFF and each --line, Threads 1 Hash 16, `go nodes N`; records the last score
   (mate n / cp) and bestmove; a position where OFF reports a mate and a line does not is a FAIL.
Exit 0 when every check passes. Uses only the standard library (no python-chess).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

FENS = ['startpos',
        'fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',
        'fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',
        'fen r1bq1rk1/pp2ppbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 9']


class Engine:
    def __init__(self, exe, log):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.log = log

    def send(self, s):
        self.log.write('> ' + s + '\n')
        self.p.stdin.write(s + '\n')
        self.p.stdin.flush()

    def wait(self, rx, keep=None, timeout=600):
        r = re.compile(rx)
        kept = []
        t0 = time.time()
        for line in self.p.stdout:
            self.log.write(line)
            if keep and re.search(keep, line):
                kept.append(line.rstrip())
            m = r.search(line)
            if m:
                return m, kept
            if time.time() - t0 > timeout:
                break
        raise SystemExit('engine stopped or timed out before ' + rx)

    def opts(self, line):
        for kv in [x for x in line.split(';') if x]:
            n, v = kv.split('=', 1)
            self.send(f'setoption name {n} value {v}')

    def legal(self, pos):
        self.send('position ' + pos)
        self.send('go perft 1')
        _, kept = self.wait(r'^nodes \d+', keep=r'^[a-h][1-8][a-h][1-8][qrbn]?: \d+')
        return {k.split(':')[0] for k in kept}

    def quit(self):
        self.send('quit')
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass


def uci_options(eng):
    eng.send('uci')
    _, kept = eng.wait(r'^uciok', keep=r'^option name ')
    out = {}
    for k in kept:
        m = re.match(r'option name (.+?) type (\S+)(?: default (\S*))?', k)
        if m:
            out[m.group(1)] = {'type': m.group(2), 'default': m.group(3), 'raw': k}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('out')
    ap.add_argument('--line', action='append', default=[])
    ap.add_argument('--new-opt', action='append', default=[], help='switch option: advertised, default OFF')
    ap.add_argument('--new-param', action='append', default=[], help='NAME=DEFAULT: advertised, default as given')
    ap.add_argument('--skip-smoke', action='store_true')
    ap.add_argument('--mate-epd', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'mate_probe.epd'))
    ap.add_argument('--mate-nodes', type=int, default=3000000)
    ap.add_argument('--movetime', type=int, default=1000)
    a = ap.parse_args()
    res = {'exe': a.exe, 'lines': a.line, 'checks': {}, 'fail': []}
    log = open(a.out + '.uci.log', 'w', newline='\n')
    eng = Engine(a.exe, log)
    # 1. option list
    opts = uci_options(eng)
    off_words = {'0', 'false', 'off', 'none', '<empty>', ''}
    rows = {}
    for n in a.new_opt:
        o = opts.get(n)
        ok = o is not None and (o['default'] or '').lower() in off_words
        rows[n] = {'advertised': o is not None, 'default': None if o is None else o['default'], 'ok': ok}
        if not ok:
            res['fail'].append(f'option {n}: {rows[n]}')
    for nv in a.new_param:
        n, v = nv.split('=', 1)
        o = opts.get(n)
        ok = o is not None and o['default'] == v
        rows[n] = {'advertised': o is not None, 'default': None if o is None else o['default'], 'expected': v, 'ok': ok}
        if not ok:
            res['fail'].append(f'param {n}: {rows[n]}')
    res['checks']['uci_options'] = rows
    # 2. movetime smoke
    smoke = []
    for line in ([] if a.skip_smoke else [''] + a.line):
        for threads in (1, 4):
            for pos in FENS:
                eng.send('ucinewgame')
                eng.send('setoption name OwnBook value false')
                eng.send(f'setoption name Threads value {threads}')
                eng.send('setoption name Hash value 16')
                eng.opts(line)
                eng.send('isready')
                eng.wait(r'^readyok')
                eng.send('position ' + pos)
                eng.send(f'go movetime {a.movetime}')
                m, kept = eng.wait(r'^bestmove (\S+)', keep=r'^info .*score ')
                best = m.group(1)
                legal = eng.legal(pos)
                ok = best in legal
                smoke.append({'line': line or 'OFF', 'threads': threads, 'pos': pos[:40], 'bestmove': best,
                              'legal': ok, 'last_info': kept[-1][:160] if kept else ''})
                if not ok:
                    res['fail'].append(f'smoke illegal bestmove {best} line={line or "OFF"} T{threads} {pos}')
    res['checks']['smoke'] = smoke
    # reset to OFF for the probe: new process per config keeps options clean
    eng.quit()
    probe = {}
    fens = [l.strip() for l in open(a.mate_epd) if l.strip()]
    for line in [''] + a.line:
        e = Engine(a.exe, log)
        uci_options(e)
        e.send('setoption name OwnBook value false')
        e.send('setoption name Hash value 16')
        e.opts(line)
        rows = []
        for fen in fens:
            e.send('ucinewgame')
            e.send('isready')
            e.wait(r'^readyok')
            e.send('position fen ' + fen)
            e.send(f'go nodes {a.mate_nodes}')
            m, kept = e.wait(r'^bestmove (\S+)', keep=r'^info .*score (mate|cp) ')
            last = kept[-1] if kept else ''
            sm = re.search(r'score (mate|cp) (-?\d+)', last)
            rows.append({'fen': fen, 'score': f'{sm.group(1)} {sm.group(2)}' if sm else '?', 'bestmove': m.group(1)})
        e.quit()
        probe[line or 'OFF'] = rows
    for line in a.line:
        for off_row, on_row in zip(probe['OFF'], probe[line]):
            if off_row['score'].startswith('mate') and not on_row['score'].startswith('mate'):
                res['fail'].append(f'mate lost: {line} {on_row["fen"]} OFF {off_row["score"]} ON {on_row["score"]}')
    res['checks']['mate_probe'] = probe
    res['summary'] = {k: sum(1 for r in v if r['score'].startswith('mate')) for k, v in probe.items()}
    res['result'] = 'PASS' if not res['fail'] else 'FAIL'
    with open(a.out, 'w', newline='\n') as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({'result': res['result'], 'mates_found': res['summary'], 'fail': res['fail'][:10],
                      'smoke_runs': len(smoke), 'options': res['checks']['uci_options']}, indent=1))
    return 0 if not res['fail'] else 1


if __name__ == '__main__':
    sys.exit(main())
