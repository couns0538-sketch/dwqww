#!/usr/bin/env python3
"""playout_check.py - root and interior consistency: from boundary roots the engine plays its side against an oracle opponent, move by move, until
the next zeroing move, mate, or the 100th half-move. Not a match: one engine, fixed depth, the other side is python-chess + tables with the exact solver.

usage: python -I -B playout_check.py <exe> <tables> <exact.jsonl> <out.jsonl> --depth 6 [--opt N=V ...] [--first N] [--jobs 3]
A row is judged when its best class is win (the engine plays the winner, the oracle the longest defence) or blessed / draw at the boundary (the engine defends,
the oracle plays the best attack: the move that keeps a win class if any, else the shortest distance).
Result: held = the engine reached the class the oracle gave at the root. win: zeroing move or mate came in time. blessed or draw: the clock reached 100 without a
loss, or the line left the tablebase win. Prints counts; exit 1 if any row is lost.
"""
import argparse
import json
import os
import queue
import sys
import threading

import chess
import chess.syzygy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_exact import Budget, Solver, RANK  # noqa: E402
from uci_tb import Engine, check_self_pin, parse_search  # noqa: E402


def oracle_move(tb, solver, b, attacker):
    """The oracle side's move: attacker keeps the best exact class with the shortest distance; defender the best class with the longest distance."""
    best = None
    best_key = None
    for m in list(b.legal_moves):
        solver.memo.clear()
        solver.reset()
        try:
            cls = solver.move_class(b, m)
        except Budget:
            cls = None
        if cls is None:
            continue
        z = b.is_zeroing(m)
        b.push(m)
        try:
            d = abs(tb.probe_dtz(b)) if not z and not b.is_game_over() else 0
        except (chess.syzygy.MissingTableError, KeyError):
            d = 0
        b.pop()
        key = (RANK[cls], -d if attacker else d)
        if best_key is None or key > best_key:
            best, best_key = m, key
    return best


def play(a, e, tb, solver, row):
    start = row['fen']
    b = chess.Board(start)
    best = row['best']
    engine_side = b.turn
    want = {2: 'win', 1: 'cursed', 0: 'draw', -1: 'blessed', -2: 'loss'}[best]
    moves = []
    plies = 0
    while True:
        if b.is_checkmate():
            return ('held' if want == 'win' and b.turn != engine_side else 'lost'), plies
        if b.is_stalemate():
            return ('held' if want in ('draw', 'blessed', 'cursed') else 'lost'), plies
        if b.halfmove_clock >= 100:
            return ('held' if want in ('draw', 'blessed', 'cursed') else 'lost'), plies
        if plies and b.halfmove_clock == 0:
            # the clock was reset: the WDL of this position now decides
            w = tb.probe_wdl(b)
            mine = w if b.turn == engine_side else -w
            if want == 'win':
                return ('held' if mine == 2 else 'lost'), plies
            return ('held' if mine > -2 else 'lost'), plies
        if b.turn == engine_side:
            e.send('position fen ' + start + (' moves ' + ' '.join(moves) if moves else ''))
            e.send(f'go depth {a.depth}')
            r = parse_search(e.read_until(lambda l: l.startswith('bestmove')))
            move = chess.Move.from_uci(r['bestmove'])
            if move not in b.legal_moves:
                return 'illegal', plies
        else:
            move = oracle_move(tb, solver, b, attacker=(want not in ('win',)))
            if move is None:
                return 'oracle_gave_up', plies
        moves.append(move.uci())
        b.push(move)
        plies += 1


def worker(a, rows, out, errors):
    e = Engine(a.exe, 600.0)
    tb = chess.syzygy.open_tablebase(a.tables)
    solver = Solver(tb, 400000, 8.0)
    try:
        e.send('uci')
        names = [l for l in e.read_until(lambda l: l == 'uciok') if l.startswith('option name')]
        e.send('setoption name Threads value 1')
        e.send('setoption name Hash value 16')
        e.send('setoption name OwnBook value false')
        for o in a.opt:
            k, v = o.split('=', 1)
            if not any(n.startswith(f'option name {k} ') for n in names):
                raise RuntimeError(f'engine does not advertise option {k}')
            e.send(f'setoption name {k} value {v}')
        e.send(f'setoption name SyzygyPath value {a.tables}')
        e.send('isready')
        e.read_until(lambda l: l == 'readyok')
        while True:
            try:
                row = rows.get_nowait()
            except queue.Empty:
                break
            e.send('ucinewgame')
            result, plies = play(a, e, tb, solver, row)
            out.put({'fen': row['fen'], 'best': row['best'], 'result': result, 'plies': plies})
        e.quit()
    except Exception as ex:
        errors.append(repr(ex))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('tables')
    ap.add_argument('exact')
    ap.add_argument('out')
    ap.add_argument('--depth', type=int, default=6)
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--first', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=3)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    check_self_pin()
    a.exe = os.path.abspath(a.exe)
    rows = queue.Queue()
    n = 0
    for line in open(a.exact, encoding='utf-8'):
        r = json.loads(line)
        if r.get('unresolved') or r.get('best') is None or r.get('castling') or r['clock'] >= 100 or ' moves ' in r['fen']:
            continue
        if r['best'] == -2 or r['best'] == 1:   # a sure loss has nothing to hold; a cursed win only draws
            continue
        if a.first and n >= a.first:
            break
        rows.put(r)
        n += 1
    out = queue.Queue()
    errors = []
    threads = [threading.Thread(target=worker, args=(a, rows, out, errors), daemon=True) for _ in range(a.jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    res = []
    while not out.empty():
        res.append(out.get())
    with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
        for r in sorted(res, key=lambda x: x['fen']):
            f.write(json.dumps(r) + '\n')
    count = {}
    for r in res:
        k = f"best{r['best']}:{r['result']}"
        count[k] = count.get(k, 0) + 1
    print(json.dumps({'rows': n, 'done': len(res), 'counts': dict(sorted(count.items()))}))
    for r in [x for x in res if x['result'] not in ('held',)][:8]:
        print('NOT HELD', r)
    for e in errors:
        print('ERROR', e)
    sys.exit(1 if errors or any(r['result'] == 'lost' or r['result'] == 'illegal' for r in res) else 0)


if __name__ == '__main__':
    main()
