#!/usr/bin/env python3
"""pins.py - bench d11-d22 net on and net off, perft 5 startpos and kiwipete, one exe, one engine per check.

usage (under pinned.ps1): python -I -B pins.py <exe> <out.json> [--expect lock|p6path|p6pd4|none] [--opt N=V ...] [--tables DIR]
        [--depths 11,13,16,20,22] [--no-net-off]
Compares with the pins given in the job prompt. Runs sequentially so that each engine has a whole CPU.
Exit 0 all equal, 1 a pin differs, 3 timeout (the engine is left running and reported, never killed).
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uci_tb import Engine, check_self_pin  # noqa: E402

LOCK_ON = [312866, 862329, 3024920, 12389307, 34048354]
LOCK_OFF = [375354, 907205, 2448617, 13573040, 24506465]
P6_PATH_ON = [313631, 866959, 2460490, 11465604, 31972996]
P6_PD4_ON = [312794, 847340, 2563760, 9925508, 28519443]
PERFT = {'startpos': ('position startpos', 4865609),
         'kiwipete': ('position fen r3k2r/p1ppqpb1/2n2np1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1', 193690690)}
# the job's canonical kiwipete is the usual one; the variant above is rejected by the check below when it fails
KIWI_CANON = 'position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'
PERFT['kiwipete'] = (KIWI_CANON, 193690690)
BENCH = re.compile(r'bench depth (\d+) nodes (\d+)')


def bench(engine, depth):
    engine.send(f'bench {depth}')
    lines = engine.read_until(lambda l: 'bench depth' in l)
    m = BENCH.search(lines[-1])
    return int(m.group(2))


def perft(engine, cmd, depth=5):
    engine.send(cmd)
    engine.send(f'go perft {depth}')
    lines = engine.read_until(lambda l: l.startswith('nodes '))
    return int(lines[-1].split()[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('out')
    ap.add_argument('--expect', default='lock')
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--tables', default='')
    ap.add_argument('--depths', default='11,13,16,20,22')
    ap.add_argument('--no-net-off', action='store_true')
    ap.add_argument('--limit-s', type=float, default=1800.0)
    a = ap.parse_args()
    if os.path.exists(a.out):
        print(f'refusing: {a.out} exists')
        sys.exit(2)
    check_self_pin()
    depths = [int(x) for x in a.depths.split(',')]
    e = Engine(os.path.abspath(a.exe), a.limit_s)
    e.send('uci')
    e.read_until(lambda l: l == 'uciok')
    for o in a.opt:
        k, v = o.split('=', 1)
        e.send(f'setoption name {k} value {v}')
    load = []
    if a.tables:
        e.send(f'setoption name SyzygyPath value {a.tables}')
    e.send('isready')
    load = [l for l in e.read_until(lambda l: l == 'readyok') if l.startswith('info string')]
    res = {'exe': os.path.abspath(a.exe), 'load': load, 'opts': a.opt, 'on': {}, 'off': {}, 'perft': {}}
    t0 = time.perf_counter()
    try:
        for d in depths:
            res['on'][str(d)] = bench(e, d)
            print(f'on d{d} {res["on"][str(d)]}', flush=True)
        if not a.no_net_off:
            e.send('setoption name UseNNUE value false')
            for d in depths:
                res['off'][str(d)] = bench(e, d)
                print(f'off d{d} {res["off"][str(d)]}', flush=True)
            e.send('setoption name UseNNUE value true')
        for name, (cmd, want) in PERFT.items():
            res['perft'][name] = perft(e, cmd)
            print(f'perft {name} {res["perft"][name]} (want {want})', flush=True)
    except TimeoutError as ex:
        print(f'TIMEOUT {ex}; engine pid {e.p.pid} left running')
        sys.exit(3)
    e.quit()
    res['secs'] = round(time.perf_counter() - t0, 1)
    want_on = {'lock': LOCK_ON, 'p6path': P6_PATH_ON, 'p6pd4': P6_PD4_ON}.get(a.expect)
    bad = []
    if want_on:
        full = [11, 13, 16, 20, 22]
        for d in depths:
            if res['on'][str(d)] != want_on[full.index(d)]:
                bad.append(f'on d{d}')
        if a.expect == 'lock' and not a.no_net_off:
            for d in depths:
                if res['off'][str(d)] != LOCK_OFF[full.index(d)]:
                    bad.append(f'off d{d}')
    for name, (cmd, want) in PERFT.items():
        if res['perft'][name] != want:
            bad.append(f'perft {name}')
    res['bad'] = bad
    json.dump(res, open(a.out, 'w'), indent=1)
    print('PINS', 'ALL EQUAL' if not bad and want_on else ('NO EXPECTATION' if not want_on and not bad else 'DIFFER ' + ' '.join(bad)))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
