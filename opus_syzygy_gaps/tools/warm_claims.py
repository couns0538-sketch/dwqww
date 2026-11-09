#!/usr/bin/env python3
"""warm_claims.py - TT state fixtures for the rule-50 handling (G7, G8). Own code. Run under pinned.ps1.

Mode clock: a line is "<six-field FEN with clock 0>\t<later clock c>\t<expected class at clock c>".
  warm: ucinewgame, search the FEN at clock 0, then (same TT) search it at clock c.
  cold: ucinewgame, search it at clock c.
A TB win / TB loss or mate score in the warm search while the expected class (from the oracle: dtz + c) is not win / loss is
a false claim. The cold search is the control.

Mode toggle: a line is "<six-field FEN>". rule 50 on: search; set Syzygy50MoveRule false without ucinewgame; search again.
cold: fresh hash with the rule off, search. Reports the rows whose warm TB class differs from the cold one. Also the other way.

usage: python -I -B warm_claims.py clock|toggle <exe> <in> <out.jsonl> --tables DIR --depth D [--jobs 4] [--opt N=V ...]
"""
import argparse
import json
import os
import queue
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_tb import Engine, check_self_pin, parse_search  # noqa: E402

TB_LOW = 31743


def cls(row):
    if row.get('score') is None:
        return 'none'
    if row['score_type'] == 'mate':
        return 'win' if row['score'] > 0 else 'loss'
    if row['score'] >= TB_LOW:
        return 'win'
    if row['score'] <= -TB_LOW:
        return 'loss'
    return 'other'


def go(e, fen, depth):
    e.send(f'position fen {fen}')
    e.send(f'go depth {depth}')
    return parse_search(e.read_until(lambda l: l.startswith('bestmove')))


def worker(a, jobs, out, errors):
    e = Engine(a.exe, 600.0)
    try:
        e.send('uci')
        names = [l for l in e.read_until(lambda l: l == 'uciok') if l.startswith('option name')]
        e.send('setoption name Threads value 1')
        e.send('setoption name Hash value 32')
        e.send('setoption name OwnBook value false')
        for o in a.opt:
            k, v = o.split('=', 1)
            if not any(n.startswith(f'option name {k} ') for n in names):
                raise RuntimeError(f'engine does not advertise option {k}')
            e.send(f'setoption name {k} value {v}')
        e.send(f'setoption name SyzygyPath value {a.tables}')
        e.send('isready')
        for l in e.read_until(lambda l: l == 'readyok'):
            if 'invalid' in l:
                raise RuntimeError(f'engine rejected an option: {l}')
        while True:
            try:
                i, line = jobs.get_nowait()
            except queue.Empty:
                break
            if a.mode == 'clock':
                fen, c, expect = line.split('\t')
                f = fen.split()
                later = ' '.join(f[:4] + [c, str(max(1, int(c) // 2 + 1))])
                e.send('ucinewgame')
                first = go(e, fen, a.depth)
                warm = go(e, later, a.depth)
                e.send('ucinewgame')
                cold = go(e, later, a.depth)
                out.put({'i': i, 'fen': later, 'expect': expect, 'first': cls(first), 'warm': cls(warm), 'cold': cls(cold),
                         'warm_score': warm['score'], 'cold_score': cold['score'], 'warm_type': warm['score_type']})
            else:
                # The control for the option change: the same sequence with a manual Clear Hash, the very call the switch makes,
                # so with the switch on warm and control must be node-identical (histories are kept in both).
                fen = line
                e.send('setoption name Syzygy50MoveRule value true')
                e.send('ucinewgame')
                on1 = go(e, fen, a.depth)
                e.send('setoption name Syzygy50MoveRule value false')
                off_warm = go(e, fen, a.depth)
                e.send('setoption name Syzygy50MoveRule value true')
                on_warm = go(e, fen, a.depth)
                e.send('setoption name Syzygy50MoveRule value true')
                e.send('ucinewgame')
                on1b = go(e, fen, a.depth)
                e.send('setoption name Syzygy50MoveRule value false')
                e.send('setoption name Clear Hash')
                off_cold = go(e, fen, a.depth)
                e.send('setoption name Syzygy50MoveRule value true')
                e.send('setoption name Clear Hash')
                on_cold = go(e, fen, a.depth)
                out.put({'i': i, 'fen': fen, 'on_first': on1['score'], 'off_warm': off_warm['score'], 'off_cold': off_cold['score'],
                         'on_warm': on_warm['score'], 'on_cold': on_cold['score'],
                         'off_warm_nodes': off_warm['nodes'], 'off_cold_nodes': off_cold['nodes'],
                         'on_warm_nodes': on_warm['nodes'], 'on_cold_nodes': on_cold['nodes'],
                         'off_warm_cls': cls(off_warm), 'off_cold_cls': cls(off_cold),
                         'on_warm_cls': cls(on_warm), 'on_cold_cls': cls(on_cold)})
        e.quit()
    except Exception as ex:
        errors.append(str(ex))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['clock', 'toggle'])
    ap.add_argument('exe')
    ap.add_argument('infile')
    ap.add_argument('out')
    ap.add_argument('--tables', required=True)
    ap.add_argument('--depth', type=int, required=True)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--opt', action='append', default=[])
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    check_self_pin()
    a.exe = os.path.abspath(a.exe)
    lines = [l.rstrip('\n') for l in open(a.infile, encoding='utf-8') if l.strip() and not l.startswith('#')]
    jobs = queue.Queue()
    for i, l in enumerate(lines):
        jobs.put((i, l))
    out = queue.Queue()
    errors = []
    threads = [threading.Thread(target=worker, args=(a, jobs, out, errors), daemon=True) for _ in range(a.jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    rows = []
    while not out.empty():
        rows.append(out.get())
    rows.sort(key=lambda r: r['i'])
    with open(a.out, 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    if a.mode == 'clock':
        false_warm = [r for r in rows if r['warm'] in ('win', 'loss') and r['warm'] != r['expect']]
        false_cold = [r for r in rows if r['cold'] in ('win', 'loss') and r['cold'] != r['expect']]
        # control rows (dtz + c = 99): a guard that rejects everything would lose these true claims
        control = [r for r in rows if r['expect'] in ('win', 'loss')]
        print(json.dumps({'rows': len(rows), 'false_warm': len(false_warm), 'false_cold': len(false_cold),
                          'first_decided': sum(r['first'] in ('win', 'loss') for r in rows),
                          'target_rows': len(rows) - len(control), 'control_rows': len(control),
                          'control_warm_true': sum(r['warm'] == r['expect'] for r in control),
                          'control_cold_true': sum(r['cold'] == r['expect'] for r in control)}))
        for r in false_warm[:8]:
            print('FALSE', r['fen'], 'expect', r['expect'], 'warm', r['warm_type'], r['warm_score'], 'cold', r['cold_score'])
    else:
        diff_off = [r for r in rows if r['off_warm_cls'] != r['off_cold_cls']]
        diff_on = [r for r in rows if r['on_warm_cls'] != r['on_cold_cls']]
        nodes_diff = [r for r in rows if r['off_warm_nodes'] != r['off_cold_nodes'] or r['on_warm_nodes'] != r['on_cold_nodes']]
        print(json.dumps({'rows': len(rows), 'off_warm_differs': len(diff_off), 'on_warm_differs': len(diff_on),
                          'rows_with_other_nodes_than_manual_clear': len(nodes_diff)}))
        for r in (diff_off + diff_on)[:8]:
            print('DIFF', r)
    for e in errors:
        print('ERROR', e)
    sys.exit(1 if errors or len(rows) != len(lines) else 0)


if __name__ == '__main__':
    main()
