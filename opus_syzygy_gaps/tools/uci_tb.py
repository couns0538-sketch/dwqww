#!/usr/bin/env python3
"""uci_tb.py - run FENs through one engine over UCI, one JSON line per position. Own code.

usage (under pinned.ps1, which sets Idle + 0xF000; this script re-reads both and fails closed):
  python -I -B uci_tb.py <exe> <fens file> <out.jsonl> [--tables DIR] [--depth D | --nodes N] [--jobs 4]
                         [--opt Name=Value ...] [--hash 32] [--warm] [--limit-s 600] [--first K]

A FEN line may carry "moves a b c" after the six FEN fields; lines starting with '#' are skipped.
Every engine: Threads 1, OwnBook false, ucinewgame before each position unless --warm.
On timeout or error the worker always quits its own child (UCI quit, then terminate if still alive); the run exits 3 on timeout.
Exit 0 = all rows written; 1 = an engine rejected a FEN or an option; 3 = timeout; 90 = pin check failed.
"""
import argparse
import ctypes
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

WANT_MASK = 0xF000
IDLE = 0x40
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
kernel32.GetCurrentProcess.restype = ctypes.c_void_p
kernel32.GetProcessAffinityMask.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
kernel32.GetPriorityClass.argtypes = [ctypes.c_void_p]
kernel32.GetPriorityClass.restype = ctypes.c_uint32


def pin_of(handle):
    mask = ctypes.c_size_t()
    system = ctypes.c_size_t()
    if not kernel32.GetProcessAffinityMask(handle, ctypes.byref(mask), ctypes.byref(system)):
        return None, None
    return mask.value, kernel32.GetPriorityClass(handle)


def check_self_pin():
    m, c = pin_of(kernel32.GetCurrentProcess())
    if m != WANT_MASK or c != IDLE:
        print(f'FAIL pin: mask {m} class {c}; run under pinned.ps1')
        sys.exit(90)


class Engine:
    def __init__(self, exe, limit_s):
        self.limit_s = limit_s
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        m, c = pin_of(ctypes.c_void_p(int(self.p._handle)))
        if m != WANT_MASK or c != IDLE:
            raise RuntimeError(f'engine pin mask {m} class {c}: refused')
        self.lines = queue.Queue()
        self.t = threading.Thread(target=self._read, daemon=True)
        self.t.start()

    def _read(self):
        for line in self.p.stdout:
            self.lines.put(line.rstrip('\r\n'))
        self.lines.put(None)

    def send(self, text):
        self.p.stdin.write(text + '\n')
        self.p.stdin.flush()

    def read_until(self, pred):
        out = []
        end = time.perf_counter() + self.limit_s
        while True:
            left = end - time.perf_counter()
            if left <= 0:
                raise TimeoutError('no answer within limit: ' + (out[-1] if out else ''))
            try:
                line = self.lines.get(timeout=left)
            except queue.Empty:
                raise TimeoutError('no answer within limit: ' + (out[-1] if out else ''))
            if line is None:
                raise RuntimeError('engine closed its output; last: ' + (out[-1] if out else ''))
            out.append(line)
            if pred(line):
                return out

    def quit(self):
        """Stop this worker's own child only: UCI quit, then terminate if still alive."""
        try:
            if self.p.poll() is None:
                try:
                    self.send('quit')
                except Exception:
                    pass
                try:
                    self.p.wait(timeout=5)
                except Exception:
                    pass
            if self.p.poll() is None:
                self.p.terminate()
                try:
                    self.p.wait(timeout=5)
                except Exception:
                    pass
            if self.p.poll() is None:
                self.p.kill()
                try:
                    self.p.wait(timeout=5)
                except Exception as e:
                    print(f'WARNING own child still alive after kill: pid {self.p.pid}: {e}')
        except Exception as e:
            print(f'WARNING quit path failed for pid {getattr(self.p, "pid", "?")}: {e}')


SCORE = re.compile(r' score (cp|mate) (-?\d+)')
DEPTH = re.compile(r'^info depth (\d+)')
NODES = re.compile(r' nodes (\d+)')
PV = re.compile(r' pv (.*)$')


def parse_search(lines):
    row = {'score_type': None, 'score': None, 'depth': None, 'nodes': None, 'pv': [], 'bestmove': None}
    invalid = [l for l in lines if 'invalid' in l]
    for l in lines:
        if l.startswith('info depth'):
            m = SCORE.search(l)
            if m:
                row['score_type'], row['score'] = m.group(1), int(m.group(2))
            d = DEPTH.search(l)
            if d:
                row['depth'] = int(d.group(1))
            n = NODES.search(l)
            if n:
                row['nodes'] = int(n.group(1))
            p = PV.search(l)
            row['pv'] = p.group(1).split() if p else []
        elif l.startswith('bestmove'):
            row['bestmove'] = l.split()[1]
    if invalid:
        row['invalid'] = invalid
    return row


def setup(engine, a):
    engine.send('uci')
    lines = engine.read_until(lambda l: l == 'uciok')
    names = [l for l in lines if l.startswith('option name')]
    engine.send('setoption name Threads value 1')
    engine.send(f'setoption name Hash value {a.hash}')
    engine.send('setoption name OwnBook value false')
    info = []
    for o in a.opt:
        k, v = o.split('=', 1)
        if not any(n.startswith(f'option name {k} ') for n in names):
            raise RuntimeError(f'engine does not advertise option {k}')
        engine.send(f'setoption name {k} value {v}')
    if a.tables:
        engine.send(f'setoption name SyzygyPath value {a.tables}')
    engine.send('isready')
    info = engine.read_until(lambda l: l == 'readyok')
    for l in info:
        if 'invalid value' in l:   # "N invalid files skipped" in the load line is a legitimate report
            raise RuntimeError(f'engine rejected an option: {l}')
    return [l for l in info if l.startswith('info string')]


def worker(idx, a, jobs, out, stop, results):
    engine = Engine(a.exe, a.limit_s)
    try:
        strings = setup(engine, a)
        results['load'].setdefault(idx, strings)
        while not stop.is_set():
            try:
                i, line = jobs.get_nowait()
            except queue.Empty:
                break
            if not a.warm:
                engine.send('ucinewgame')
            parts = line.split(' moves ')
            cmd = f'position fen {parts[0]}' + (f' moves {parts[1]}' if len(parts) > 1 else '')
            engine.send(cmd)
            limit = f'depth {a.depth}' if a.depth else f'nodes {a.nodes}'
            engine.send(f'go {limit}')
            lines = engine.read_until(lambda l: l.startswith('bestmove'))
            row = parse_search(lines)
            row.update(i=i, fen=line)
            if 'invalid' in row:
                results['invalid'] += 1
            out.put(row)
    except TimeoutError as e:
        results['timeout'] += 1
        results['errors'].append(f'worker {idx}: {e}')
        stop.set()
    except Exception as e:
        results['errors'].append(f'worker {idx}: {e}')
        stop.set()
    finally:
        engine.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('fens')
    ap.add_argument('out')
    ap.add_argument('--tables', default='')
    ap.add_argument('--depth', type=int, default=0)
    ap.add_argument('--nodes', type=int, default=0)
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--opt', action='append', default=[])
    ap.add_argument('--hash', type=int, default=32)
    ap.add_argument('--warm', action='store_true')
    ap.add_argument('--limit-s', type=float, default=600.0)
    ap.add_argument('--first', type=int, default=0)
    a = ap.parse_args()
    if bool(a.depth) == bool(a.nodes):
        ap.error('give exactly one of --depth, --nodes')
    if a.jobs > 4:
        ap.error('at most 4 engines: CPUs 12-15')
    if os.path.exists(a.out):
        print(f'refusing: {a.out} exists')
        sys.exit(2)
    check_self_pin()
    a.exe = os.path.abspath(a.exe)
    fens = [l.strip() for l in open(a.fens, encoding='utf-8') if l.strip() and not l.startswith('#')]
    if a.first:
        fens = fens[:a.first]
    jobs = queue.Queue()
    for i, f in enumerate(fens):
        jobs.put((i, f))
    out = queue.Queue()
    stop = threading.Event()
    results = {'load': {}, 'invalid': 0, 'timeout': 0, 'errors': []}
    threads = [threading.Thread(target=worker, args=(k, a, jobs, out, stop, results), daemon=True) for k in range(a.jobs)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    rows = {}
    with open(a.out + '.tmp', 'w', encoding='utf-8') as f:
        while any(t.is_alive() for t in threads) or not out.empty():
            try:
                row = out.get(timeout=1.0)
            except queue.Empty:
                continue
            rows[row['i']] = row
            f.write(json.dumps(row) + '\n')
    for t in threads:
        t.join(timeout=5)
    with open(a.out, 'w', encoding='utf-8') as f:
        for i in sorted(rows):
            f.write(json.dumps(rows[i]) + '\n')
    os.replace(a.out + '.tmp', a.out + '.unsorted')
    load = sorted({s for v in results['load'].values() for s in v})
    print(f'rows {len(rows)}/{len(fens)} secs {time.perf_counter() - t0:.1f} invalid {results["invalid"]} '
          f'timeouts {results["timeout"]} load {load}')
    for e in results['errors']:
        print('ERROR', e)
    if results['timeout']:
        sys.exit(3)
    if results['errors'] or results['invalid'] or len(rows) != len(fens):
        sys.exit(1)


if __name__ == '__main__':
    main()
