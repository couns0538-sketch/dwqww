#!/usr/bin/env python3
"""warm_identity.py - warm-table identity of a candidate exe against the lock (speed job, own code).

usage: python -I -B warm_identity.py <ref exe> <cand exe> <fens file> <out dir> [--n 400] [--nodes 20000] [--tables DIR]
(job copy: mask 0xF000, --tables added, this job's three option lines ignored in the comparison.)

The bit-exact proof (bitexact_check L3) sends ucinewgame before every FEN, so the TT is always cold there. This tool
plays ONE script into each exe with the table kept warm across positions (no ucinewgame), so TT aging / replacement
and the lease / owned-path flag are exercised across option changes, as the independent patch review asked (its QA
tests 1, 2 and 8):
  - first command `bench 1`, then `go perft 1` (tables built before any position; robustness);
  - uci, OwnBook false; for each of the first N FENs: `position fen <fen>` + `go nodes <nodes>` (Threads 1), waiting
    for bestmove before the next line (a `go` is aborted by the next UCI line in this engine);
  - every 25 FENs one state change from a fixed cycle: Hash 1, Hash 64, Clear Hash, UseNNUE false, UseNNUE true,
    Hash 16;
  - at the end `bench 13` (its node count must be the lock pin 862329 on both) and quit;
  - fail closed (exit 1) on any `info string ... invalid` line after a `position`: the engine keeps its PREVIOUS position
    on a rejected FEN, so both exes would agree on the wrong position (the withdrawn placement-only L3 of 09:2x); the
    reference result rows must also not be degenerate (n >= 100 and fewer than n / 10 distinct rows = exit 1), as in
    bitexact_check L3 (Code Review SHOULD 'warm_identity invalid-FEN').
Both transcripts are normalised (the `nps` and `time` fields removed from info lines, bench timing fields too) and
compared line by line. Exit 0 = identical, 3 = a difference (first one printed), 1 = error. Placement (Code Review
SHOULD 'warm_identity self-pin'): before the out dir, the FEN file or any engine, this process sets its own CPU mask
0x3 (CPUs 0-1, the job's check pair) and the Idle class and reads both back; every engine it starts inherits both and
is read back too (on its process handle, before its first command). A failed call or a mismatch is exit 1 (fail
closed): no comparison runs on a process that is not pinned. Reads the exes and the FEN file only; writes only
<out dir>.
"""
import ctypes
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time
from ctypes import wintypes

MASK = 0xF000    # this job: CPUs 12-15 (copy of opus_speed/tools/warm_identity.py, only this constant changed)
IDLE = 0x40   # IDLE_PRIORITY_CLASS
CYCLE = ['setoption name Hash value 1', 'setoption name Hash value 64', 'setoption name Clear Hash',
         'setoption name UseNNUE value false', 'setoption name UseNNUE value true', 'setoption name Hash value 16']
STRIP = re.compile(r' (nps|time) \d+')


def kernel32():
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.GetCurrentProcess.restype = wintypes.HANDLE
    k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.SetPriorityClass.restype = wintypes.BOOL
    k32.GetPriorityClass.argtypes = [wintypes.HANDLE]
    k32.GetPriorityClass.restype = wintypes.DWORD
    k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    k32.SetProcessAffinityMask.restype = wintypes.BOOL
    k32.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    k32.GetProcessAffinityMask.restype = wintypes.BOOL
    return k32


def read_back(k32, h, what):
    """The CPU mask and priority class of process handle h must be MASK and Idle, else fail closed (Code Review
    SHOULD 'warm_identity self-pin')."""
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if not k32.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm)):
        raise RuntimeError(f'{what}: GetProcessAffinityMask failed (error {ctypes.get_last_error()}) - not pinned')
    pc = k32.GetPriorityClass(h)
    if pm.value != MASK or pc != IDLE:
        raise RuntimeError(f'{what}: mask 0x{pm.value:X} class 0x{pc:X}, want mask 0x{MASK:X} Idle (0x40) - not pinned')
    return f'{what}: mask 0x{MASK:X} Idle (read back)'


def place():
    """Idle class + MASK on this process, read back; engines started afterwards inherit both (and are read back)."""
    k32 = kernel32()
    h = k32.GetCurrentProcess()
    if not k32.SetPriorityClass(h, IDLE) or not k32.SetProcessAffinityMask(h, MASK):
        raise RuntimeError(f'placement failed (error {ctypes.get_last_error()}) - not pinned')
    return k32, read_back(k32, h, 'placement')


class Engine:
    # Lines come through a reader thread and a queue, so a missing line ends in a timeout instead of a blocked
    # readline (13:21 first attempt: `bench` prints "info string bench depth ...", a startswith test never matched
    # and the driver waited forever). On any error the engine gets `quit` and EOF; it is never killed.
    def __init__(self, exe, log):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)
        self.log = log
        self.q = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in iter(self.p.stdout.readline, ''):
            self.q.put(raw.rstrip('\r\n'))
        self.q.put(None)

    def send(self, line):
        self.log.append('> ' + line)
        self.p.stdin.write(line + '\n')
        self.p.stdin.flush()

    def until(self, pred, timeout=300):
        t_end = time.time() + timeout
        while True:
            try:
                line = self.q.get(timeout=max(0.1, t_end - time.time()))
            except queue.Empty:
                raise RuntimeError(f'timeout ({timeout} s) waiting for engine output; last line: {self.log[-1] if self.log else ""}')
            if line is None:
                raise RuntimeError('engine closed its output')
            self.log.append(line)
            if pred(line):
                return line

    def close(self):
        try:
            self.send('quit')
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass

    def sync(self):
        self.send('isready')
        self.until(lambda s: s == 'readyok')


def run(exe, fens, nodes, k32, tables=''):
    log = []
    e = Engine(exe, log)
    try:
        # the engine inherits this process's mask + class: read both back on its own handle before its first command
        # (printed only, never part of the compared transcript; a mismatch leaves through close(): quit + EOF)
        print(read_back(k32, int(e.p._handle), f'engine PID {e.p.pid}'), flush=True)
        e.send('bench 1')
        e.until(lambda s: 'bench depth' in s)
        e.send('go perft 1')
        e.until(lambda s: s.lower().startswith('nodes') or s.lower().startswith('perft'))
        e.send('uci')
        e.until(lambda s: s == 'uciok')
        e.send('setoption name OwnBook value false')
        if tables:
            e.send('setoption name SyzygyPath value ' + tables)
        e.sync()
        rows = []
        for i, fen in enumerate(fens):
            if i and i % 25 == 0:
                e.send(CYCLE[(i // 25 - 1) % len(CYCLE)])
                e.sync()
            mark = len(log)
            e.send('position fen ' + fen)
            e.send(f'go nodes {nodes}')
            best = e.until(lambda s: s.startswith('bestmove'))
            # a rejected FEN ('info string invalid FEN: <reason>') leaves the engine on its previous position and the
            # search below runs there on BOTH exes: never compare, fail closed (Code Review SHOULD 'warm_identity invalid-FEN')
            bad = [s for s in log[mark:] if s.startswith('info string') and 'invalid' in s]
            if bad:
                raise RuntimeError(f'engine rejected FEN {i} ({fen}): {bad[0]}')
            last = [s for s in log[mark:] if s.startswith('info depth ')]
            rows.append(STRIP.sub('', last[-1]) + ' | ' + best if last else best)
        e.send('bench 13')
        bench = e.until(lambda s: 'bench depth' in s)
    finally:
        e.close()
    return log, bench, rows


def norm(lines):
    out = []
    for s in lines:
        if s.startswith('info') or 'bench depth' in s:
            s = STRIP.sub('', s)
        if s.startswith('id name') or s.startswith('id author'):
            continue
        # this job's switches exist only in the candidate's option list (macros on, -Expose); their defaults are checked elsewhere
        if s.startswith(('option name SyzygyTbBounds ', 'option name SyzygyRootExact ', 'option name SyzygyRule50 ')):
            continue
        out.append(s)
    return out


def main():
    a = sys.argv[1:]
    n, nodes = 400, 20000
    if '--n' in a:
        i = a.index('--n'); n = int(a[i + 1]); del a[i:i + 2]
    if '--nodes' in a:
        i = a.index('--nodes'); nodes = int(a[i + 1]); del a[i:i + 2]
    tables = ''
    if '--tables' in a:
        i = a.index('--tables'); tables = a[i + 1]; del a[i:i + 2]
    if len(a) != 4:
        print(__doc__)
        return 1
    ref, cand, fenf, out = a
    k32, placed = place()          # before the out dir, the FEN file and any engine (fail closed)
    print(placed, flush=True)
    outd = pathlib.Path(out)
    outd.mkdir(parents=True, exist_ok=False)
    fens = [l.strip() for l in open(fenf, encoding='utf-8') if l.strip() and not l.startswith('#')][:n]
    res = {}
    for tag, exe in (('ref', ref), ('cand', cand)):
        t0 = time.time()
        log, bench, rows = run(exe, fens, nodes, k32, tables)
        (outd / f'{tag}.log').write_text('\n'.join(log) + '\n', encoding='utf-8', newline='\n')
        res[tag] = (norm(log), bench, time.time() - t0)
        print(f'{tag}: {len(log)} lines, {time.time() - t0:.0f} s, last bench: {bench}')
        if tag == 'ref':
            # degenerate-reference guard as in bitexact_check L3: a list that searches (almost) one position is no proof
            distinct = len(set(rows))
            if len(rows) >= 100 and distinct < len(rows) // 10:
                raise RuntimeError(f'degenerate reference: only {distinct} distinct result rows for {len(rows)} FENs')
            print(f'ref: {distinct} distinct result rows (depth / score / nodes / bestmove) for {len(rows)} FENs')
    r, c = res['ref'][0], res['cand'][0]
    searches = sum(1 for s in r if s.startswith('bestmove'))
    diff = next((i for i, (x, y) in enumerate(zip(r, c)) if x != y), None)
    if diff is None and len(r) != len(c):
        diff = min(len(r), len(c))
    pin = '862329'
    bench_ok = all(f'nodes {pin}' in res[t][1] for t in ('ref', 'cand'))
    if tables:  # with tables loaded the pin is another one: both must simply agree (nps and time are stripped)
        bench_ok = STRIP.sub('', res['ref'][1]) == STRIP.sub('', res['cand'][1])
    if diff is None and bench_ok:
        print(f'IDENTICAL: {len(r)} normalised lines, {searches} searches (go nodes {nodes}, {len(fens)} FENs, warm TT, '
              f'{len(fens) // 25} state changes), bench 13 = {pin} on both')
        return 0
    if diff is not None:
        print(f'DIFFERENT at normalised line {diff}:\n  ref : {r[diff] if diff < len(r) else "<end>"}\n  cand: {c[diff] if diff < len(c) else "<end>"}')
    if not bench_ok:
        print('bench 13 after the script is not the pin on both:', res['ref'][1], '|', res['cand'][1])
    return 3


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - report and exit 1
        print('ERROR:', exc)
        sys.exit(1)
