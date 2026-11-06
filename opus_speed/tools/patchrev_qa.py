#!/usr/bin/env python3
"""patchrev_qa.py - the patch review's remaining QA tests, lock vs the six stacks (speed job follow-up, own code).

usage: python -I -B patchrev_qa.py <test> --out <new dir> [--mask 0xC] [--stacks name,name,..] [test options]
  replay    (1a) one gate game replayed ply by ply: `position startpos moves m1..mk` + `go depth 10`, no ucinewgame, so
            later searches reuse warm subtrees (TT aging / replacement on entries that are hit); pass 2 replays the same
            list on the aged table with Hash 1 / Hash 64 / Clear Hash / UseNNUE false / UseNNUE true / Hash 16 every 10
            plies; UseNNUE true + bench 13 at the end. Deterministic at Threads 1: normalised transcripts must equal the
            lock's (the lock runs first and last as a determinism check). Options: --pgn, --game 379, --depth 10.
  protocol  (1b) per exe, Ponder true: go infinite -> stop; go ponder movetime 300 -> ponderhit; go ponder wtime/btime
            -> stop; go ponder depth 3 (finished, must wait) -> ponderhit; go mate 3 (mate in 3 and mate in 1);
            20 x go movetime 100 without ucinewgame; stop / ponderhit while idle; bench 13; quit. No bestmove before
            stop / ponderhit, every bestmove and ponder move legal (python-chess), bestmove within 5 s of stop /
            ponderhit, exit code 0; the deterministic parts (after ucinewgame) must equal the lock's.
  soak      (1c) --mask 0xF: 60 game positions x go movetime 300, Threads 2 -> 3 -> 4 before every search, Hash every 10
            searches, one Clear Hash; every bestmove legal and in time; then Threads 1, Hash 32 and 50 FENs with
            ucinewgame + go depth 13 that must equal the lock's cached L3 reference rows and the lock's own tail;
            bench 13 = 862329; exit 0. The timed Threads 2-4 searches are never compared line by line.
            SOAK ONLY: no node identity is possible at Threads > 1 and no TSan exists here - not a lock proof.
            Mask 0xF (four threads need four logical CPUs) is the job's ONE sanctioned use of CPUs 2-3 besides nps
            timing: like every mask here that touches CPUs 2-3 it is taken only while this process holds abba.ps1's
            named timing mutex (below), so a soak never runs beside an ABBA.
  extreme   (1e) data/extreme_fens.tsv: set A (accepted) ucinewgame + go depth 8 + go perft 3; set R (illegal in normal
            play) must be rejected with the expected `info string invalid FEN: <reason>` and keep the previous position
            (go perft 1). g++ group (lock, stack kit exes, stack UBSan-trap exes) and MSVC group (ASan build of the lock
            source, stack ASan exes) must each equal their lock transcript, perft equal across groups, no sanitizer line,
            exit 0.
Every engine is started by this process, which first sets its own CPU mask (inside CPUs 0-3) and Idle class and reads
both back (fail closed); engines inherit both. A mask that touches CPUs 2-3 (the ABBA timing CPU and its SMT sibling;
job rule: checks on 0x3, timing on CPU 2, CPU 3 free) is used only while this process holds the named mutex
Local\\ospd_abba_timing that abba.ps1 holds during a timing run (--mutex-wait-min, default 240 like abba.ps1; 0 = refuse
at once); it is acquired before the first engine starts and released at exit (Code Review SHOULD 'patchrev soak mask
0xF'). Engines are never killed: every run ends with stop, quit, stdin close and a 30 s wait; a process still alive
then is reported as a survivor with its PID. Writes only under --out.
Exit 0 = every exe PASS, 3 = a FAIL, 1 = error (incl. a refused mask).
"""
import argparse
import atexit
import ctypes
import glob
import hashlib
import os
import pathlib
import queue
import re
import subprocess
import sys
import threading
import time
from ctypes import wintypes

import chess
import chess.pgn

LOCK_SHA = 'fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072'
LOCK = 'F:/ospd/qa2/bin/lock_fd3a5190.exe'
LOCK_ASAN = 'F:/ospd/packs/b2_nzm1/bitexact/san/ref_asan_msvc.exe'
TIMING_MUTEX = 'Local\\ospd_abba_timing'   # abba.ps1's named mutex: one timing run at a time on this PC
TIMING_CPUS = 0xC                          # CPUs 2 (nps timing) and 3 (its SMT sibling, kept free of own work)
STACKS = ['stack_w1', 'stack_w2', 'stack_w3', 'stack_w4', 'stack_w5', 'trial_w6']
DATA = pathlib.Path(__file__).resolve().parent.parent / 'data'
PIN13 = '862329'
CYCLE = ['setoption name Hash value 1', 'setoption name Hash value 64', 'setoption name Clear Hash',
         'setoption name UseNNUE value false', 'setoption name UseNNUE value true', 'setoption name Hash value 16']
STRIP = re.compile(r' (nps|time) \d+')
SAN_RX = re.compile(r'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error|SUMMARY:|==\d+==ERROR')
INFO_RX = re.compile(r'^info depth (\d+) .*? score (cp -?\d+|mate -?\d+)(?: (?:lowerbound|upperbound))? nodes (\d+)')


def san_dir(stack):
    # trial_w6's sanitizer exes of record are the /D__BMI2__ re-run (OWN_CHECKS #6)
    return f'F:/ospd/packs/{stack}/bitexact{"_l4_bmi2" if stack == "trial_w6" else ""}/san'


def kit_exe(stack):
    return f'F:/ospd/packs/{stack}/forge_{stack}.exe'


class Timeout(Exception):
    pass


class EngineClosed(Exception):
    pass


def place(mask):
    """Idle class + CPU mask on this process, read back; any failure ends the run (fail closed)."""
    if mask <= 0 or mask & ~0xF:
        raise SystemExit(f'mask 0x{mask:X} is outside CPUs 0-3')
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
    h = k32.GetCurrentProcess()
    if not k32.SetPriorityClass(h, 0x40) or not k32.SetProcessAffinityMask(h, mask):
        raise SystemExit(f'placement failed (error {ctypes.get_last_error()})')
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if not k32.GetProcessAffinityMask(h, ctypes.byref(pm), ctypes.byref(sm)) or pm.value != mask:
        raise SystemExit(f'affinity not applied (got 0x{pm.value:X})')
    if k32.GetPriorityClass(h) != 0x40:
        raise SystemExit('Idle class not applied')
    return f'placement mask 0x{mask:X} Idle (pid {os.getpid()})'


def hold_timing_mutex(mask, wait_min):
    """A mask that touches CPUs 2-3 runs only while holding abba.ps1's timing mutex, so it never overlaps an ABBA (Code
    Review SHOULD 'patchrev soak mask 0xF'). Returns a release function (a no-op for masks inside 0x3). WAIT_ABANDONED
    counts as acquired, like abba.ps1's AbandonedMutexException; WAIT_TIMEOUT refuses the run before any engine starts."""
    if not mask & TIMING_CPUS:
        return lambda: None
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    k32.CreateMutexW.restype = wintypes.HANDLE
    k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k32.WaitForSingleObject.restype = wintypes.DWORD
    k32.ReleaseMutex.argtypes = [wintypes.HANDLE]
    k32.ReleaseMutex.restype = wintypes.BOOL
    h = k32.CreateMutexW(None, False, TIMING_MUTEX)
    if not h:
        raise SystemExit(f'cannot open the timing mutex {TIMING_MUTEX} (error {ctypes.get_last_error()})')
    rc = k32.WaitForSingleObject(h, int(wait_min * 60000))
    if rc not in (0x0, 0x80):   # WAIT_OBJECT_0, WAIT_ABANDONED
        raise SystemExit(f'mask 0x{mask:X} touches CPUs 2-3 but an ABBA timing run holds {TIMING_MUTEX} '
                         f'(waited {wait_min:g} min, wait result 0x{rc:X}): run later, or on a mask inside 0x3')
    return lambda: k32.ReleaseMutex(h)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5(path):
    return hashlib.md5(pathlib.Path(path).read_bytes()).hexdigest()


def msvc_env():
    dlls = sorted(glob.glob('C:/Program Files*/Microsoft Visual Studio/*/*/VC/Tools/MSVC/*/bin/Hostx64/x64/'
                            'clang_rt.asan_dynamic-x86_64.dll'))
    if not dlls:
        raise SystemExit('MSVC ASan runtime DLL not found')
    env = dict(os.environ)
    env['PATH'] = str(pathlib.Path(dlls[-1]).parent) + os.pathsep + env.get('PATH', '')
    env['ASAN_OPTIONS'] = 'halt_on_error=1:detect_leaks=0'
    return env


class Engine:
    """UCI process with a reader thread; lines arrive through a queue, so a missing line is a timeout, never a hang."""

    def __init__(self, exe, cwd, env=None):
        self.log = []
        self.exe = exe
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1, encoding='utf-8', errors='replace', cwd=cwd, env=env)
        self.q = queue.Queue()
        self.closed = False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            for raw in iter(self.p.stdout.readline, ''):
                self.q.put((time.perf_counter(), raw.rstrip('\r\n')))
        finally:
            self.q.put((time.perf_counter(), None))

    def send(self, line):
        self.log.append('> ' + line)
        self.p.stdin.write(line + '\n')
        self.p.stdin.flush()

    def get(self, timeout):
        if self.closed:
            raise EngineClosed(f'engine output closed (exit {self.p.poll()})')
        try:
            ts, line = self.q.get(timeout=max(0.01, timeout))
        except queue.Empty:
            raise Timeout(f'no engine output for {timeout:.1f} s')
        if line is None:
            self.closed = True
            raise EngineClosed(f'engine output closed (exit {self.p.poll()})')
        self.log.append(line)
        return ts, line

    def until(self, pred, timeout, what='line'):
        end = time.perf_counter() + timeout
        while True:
            left = end - time.perf_counter()
            if left <= 0:
                raise Timeout(f'timeout {timeout} s waiting for {what}')
            try:
                ts, line = self.get(left)
            except Timeout:
                raise Timeout(f'timeout {timeout} s waiting for {what}')
            if pred(line):
                return ts, line

    def drain(self, seconds):
        """Every line that arrives within `seconds` while nothing is sent."""
        out, end = [], time.perf_counter() + seconds
        while True:
            left = end - time.perf_counter()
            if left <= 0:
                return out
            try:
                out.append(self.get(left)[1])
            except Timeout:
                return out

    def sync(self, timeout=120):
        self.send('isready')
        return self.until(lambda s: s == 'readyok', timeout, 'readyok')

    def collect_sync(self, timeout=120):
        """Lines up to readyok (the readyok excluded)."""
        self.send('isready')
        out = []
        end = time.perf_counter() + timeout
        while True:
            line = self.get(end - time.perf_counter())[1]
            if line == 'readyok':
                return out
            out.append(line)

    def search(self, go, timeout):
        self.send(go)
        start = len(self.log)
        _, line = self.until(lambda s: s.startswith('bestmove'), timeout, 'bestmove')
        return line, self.log[start:]

    def close(self):
        """stop, quit, EOF, 30 s wait; never kills. Returns (exit code or None, pid)."""
        for cmd in ('stop', 'quit'):
            try:
                self.send(cmd)
            except (OSError, ValueError):
                pass
        try:
            self.p.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            rc = self.p.wait(timeout=30)
        except subprocess.TimeoutExpired:
            rc = None
        return rc, self.p.pid


def norm(lines):
    out = []
    for s in lines:
        if s.startswith('id name') or s.startswith('id author'):
            continue
        if s.startswith('info') or 'bench depth' in s:
            s = STRIP.sub('', s)
        out.append(s)
    return out


def first_diff(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def legal(fen, moves, best_line):
    """(ok, detail) for a 'bestmove X [ponder Y]' line in the position fen + moves."""
    parts = best_line.split()
    bm = parts[1] if len(parts) > 1 else ''
    pd = parts[3] if len(parts) > 3 and parts[2] == 'ponder' else None
    b = chess.Board() if fen == 'startpos' else chess.Board(fen)
    for m in moves:
        b.push_uci(m)
    lm = {m.uci() for m in b.legal_moves}
    if not lm:
        return bm in ('0000', '(none)'), f'no legal move, bestmove {bm}'
    if bm not in lm:
        return False, f'bestmove {bm} not legal'
    if pd is not None:
        b.push_uci(bm)
        if pd not in {m.uci() for m in b.legal_moves}:
            return False, f'ponder {pd} not legal after {bm}'
    return True, ''


def write(path, lines):
    path = pathlib.Path(path)
    if path.exists():
        raise SystemExit(f'refusing to overwrite {path}')
    path.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))


class Result:
    def __init__(self, name, exe):
        self.name, self.exe, self.fails, self.notes = name, exe, [], []
        self.rc = self.pid = None
        self.det, self.perft = [], []   # deterministic parts, filled by the scripts that have them

    def fail(self, msg):
        self.fails.append(msg)

    @property
    def verdict(self):
        return 'PASS' if not self.fails and self.rc == 0 else 'FAIL'


def run_one(name, exe, out, script, env=None):
    """Start exe, run script(engine, result), close; the transcript goes to <out>/<name>.log."""
    r = Result(name, exe)
    e = Engine(exe, str(out), env)
    try:
        script(e, r)
    except (Timeout, EngineClosed, OSError) as exc:
        r.fail(f'{type(exc).__name__}: {exc}')
    finally:
        r.rc, r.pid = e.close()
        if r.rc is None:
            r.fail(f'SURVIVOR: pid {r.pid} still running 30 s after quit (left alone, no-kill rule)')
        elif r.rc != 0:
            r.fail(f'exit code {r.rc}')
        r.log = e.log
        write(out / f'{name}.log', e.log)
    sl = [s for s in r.log if not s.startswith('> ') and SAN_RX.search(s)]
    if sl:
        r.fail(f'{len(sl)} sanitizer line(s), first: {sl[0][:160]}')
    return r


def uci_init(e, opts):
    e.send('uci')
    e.until(lambda s: s == 'uciok', 60, 'uciok')
    for o in opts:
        e.send(o)
    e.sync()


# ---------------------------------------------------------------- 1a replay
def load_game(pgn, gi):
    offs = []
    with open(pgn, encoding='utf-8', errors='replace') as f:
        while True:
            off = f.tell()
            if chess.pgn.read_headers(f) is None:
                break
            offs.append(off)
        f.seek(offs[gi])
        g = chess.pgn.read_game(f)
    if g is None or g.errors:
        raise SystemExit(f'game {gi} unreadable')
    if 'FEN' in g.headers or g.headers.get('SetUp') == '1':
        raise SystemExit(f'game {gi} does not start from the start position')
    return [m.uci() for m in g.mainline_moves()], len(offs), g.headers.get('Result', '?')


def replay_script(moves, depth, every):
    def script(e, r):
        uci_init(e, ['setoption name OwnBook value false', 'setoption name Ponder value false',
                     'setoption name Hash value 32'])
        for pas in (1, 2):
            for k in range(len(moves) + 1):
                if pas == 2 and k and k % every == 0:
                    e.send(CYCLE[(k // every - 1) % len(CYCLE)])
                    e.sync()
                e.send('position startpos' + (' moves ' + ' '.join(moves[:k]) if k else ''))
                line, _ = e.search(f'go depth {depth}', 600)
                ok, det = legal('startpos', moves[:k], line)
                if not ok:
                    r.fail(f'pass {pas} ply {k}: {det}')
        e.send('setoption name UseNNUE value true')
        e.sync()
        e.send('bench 13')
        _, b = e.until(lambda s: 'bench depth' in s, 600, 'bench 13')
        r.bench = b
        if f'nodes {PIN13}' not in b:
            r.fail(f'bench 13 not {PIN13}: {b}')
    return script


# ---------------------------------------------------------------- 1b protocol
M3 = '8/8/7k/1R6/8/8/8/R5K1 w - - 0 1'      # two rooks: 1.Ra6+ 2.Rb7+ 3.Ra8# (built for this test)
M1 = '6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1'  # back-rank mate in 1: Rd8#


def game_rows(n0, n1):
    rows = [l.rstrip('\n').split('\t') for l in open(DATA / 'game_positions_300.tsv', encoding='utf-8')
            if l.strip() and not l.startswith('#')]
    return [x[2] for x in rows[n0:n1]]


def protocol_script(fens20):
    def script(e, r):
        uci_init(e, ['setoption name OwnBook value false', 'setoption name Ponder value true'])
        r.det = []

        def no_best(lines, what):
            if any(s.startswith('bestmove') for s in lines):
                r.fail(f'{what}: bestmove before stop / ponderhit')

        def answer(fen, moves, what, cmd, timeout=5.0):
            # the clock is read before the command goes out (perf_counter: Windows monotonic() ticks in ~15.6 ms)
            t_sent = time.perf_counter()
            e.send(cmd)
            ts, line = e.until(lambda s: s.startswith('bestmove'), timeout, f'{what} bestmove')
            lat = ts - t_sent
            ok, det = legal(fen, moves, line)
            if not ok:
                r.fail(f'{what}: {det}')
            r.notes.append(f'{what} {lat * 1000:.0f} ms')
            return line

        # S1 go infinite -> stop
        e.send('position startpos moves e2e4')
        e.send('go infinite')
        no_best(e.drain(0.3), 'S1 infinite')
        answer('startpos', ['e2e4'], 'S1 infinite->stop', 'stop')
        # S2 go ponder movetime 300 -> ponderhit (the budget starts at ponderhit)
        e.send('position fen ' + fens20[0])
        e.send('go ponder movetime 300')
        no_best(e.drain(0.5), 'S2 ponder')
        answer(fens20[0], [], 'S2 ponder->ponderhit', 'ponderhit', 5.3)
        # S3 go ponder with clock -> stop
        e.send('position fen ' + fens20[1])
        e.send('go ponder wtime 3000 btime 3000')
        no_best(e.drain(0.3), 'S3 ponder')
        answer(fens20[1], [], 'S3 ponder->stop', 'stop')
        # S4 go ponder depth 3: the search ends early but must wait for ponderhit (deterministic after ucinewgame)
        e.send('ucinewgame')
        e.sync()
        e.send('position fen ' + fens20[2])
        mark = len(e.log)
        e.send('go ponder depth 3')
        got = e.drain(1.0)
        no_best(got, 'S4 ponder depth 3')
        if not any(s.startswith('info depth 3 ') for s in got):
            r.fail('S4: depth 3 not finished within 1 s')
        answer(fens20[2], [], 'S4 ponder depth 3->ponderhit', 'ponderhit')
        r.det += norm(e.log[mark:])
        # S5 / S6 go mate 3 (deterministic after ucinewgame)
        for tag, fen in (('S5 mate3', M3), ('S6 mate1', M1)):
            e.send('ucinewgame')
            e.sync()
            e.send('position fen ' + fen)
            mark = len(e.log)
            line, seg = e.search('go mate 3', 120)
            ok, det = legal(fen, [], line)
            if not ok:
                r.fail(f'{tag}: {det}')
            last = [s for s in seg if s.startswith('info depth ')]
            sc = INFO_RX.match(last[-1]).group(2) if last and INFO_RX.match(last[-1]) else '?'
            r.notes.append(f'{tag} {sc} {line}')
            if not sc.startswith('mate '):
                r.fail(f'{tag}: no mate score ({sc})')
            r.det += norm(e.log[mark:])
        # S7 20 x go movetime 100, no ucinewgame
        worst = 0.0
        for i, fen in enumerate(fens20):
            e.send('position fen ' + fen)
            t0 = time.perf_counter()
            e.send('go movetime 100')
            ts, line = e.until(lambda s: s.startswith('bestmove'), 5.1, f'S7 movetime #{i} bestmove')
            worst = max(worst, ts - t0)
            ok, det = legal(fen, [], line)
            if not ok:
                r.fail(f'S7 #{i}: {det}')
        r.notes.append(f'S7 20 x movetime 100 worst {worst * 1000:.0f} ms')
        # S8 stop / ponderhit while idle: ignored, engine answers isready
        for cmd in ('stop', 'ponderhit'):
            e.send(cmd)
            extra = e.collect_sync(5)
            if any(s.startswith('bestmove') for s in extra):
                r.fail(f'S8: {cmd} while idle printed a bestmove')
        # S9 bench 13
        e.send('bench 13')
        _, b = e.until(lambda s: 'bench depth' in s, 600, 'bench 13')
        if f'nodes {PIN13}' not in b:
            r.fail(f'bench 13 not {PIN13}: {b}')
    return script


# ---------------------------------------------------------------- 1c soak
HASHES = [1, 64, 16, 128, 32, 8]


def soak_script(pos60, fens50, ref_rows, movetime):
    def script(e, r):
        uci_init(e, ['setoption name OwnBook value false'])
        worst, late = 0.0, 0
        for i, fen in enumerate(pos60):
            e.send(f'setoption name Threads value {2 + i % 3}')
            if i % 10 == 0:
                e.send(f'setoption name Hash value {HASHES[(i // 10) % len(HASHES)]}')
            if i == 30:
                e.send('setoption name Clear Hash')
            e.sync()
            e.send('position fen ' + fen)
            t0 = time.perf_counter()
            e.send(f'go movetime {movetime}')
            ts, line = e.until(lambda s: s.startswith('bestmove'), movetime / 1000 + 10, f'soak #{i} bestmove')
            dt = ts - t0
            worst = max(worst, dt)
            if dt > movetime / 1000 + 3:
                late += 1
            ok, det = legal(fen, [], line)
            if not ok:
                r.fail(f'soak #{i} (Threads {2 + i % 3}): {det}')
        if late:
            r.fail(f'{late} searches later than movetime + 3 s')
        r.notes.append(f'{len(pos60)} searches Threads 2/3/4, worst {worst * 1000:.0f} ms')
        e.send('setoption name Threads value 1')
        e.send('setoption name Hash value 32')
        e.sync()
        same = 0
        r.det = []
        for j, fen in enumerate(fens50):
            e.send('ucinewgame')
            e.sync()
            e.send('position fen ' + fen)
            line, seg = e.search('go depth 13', 600)
            last = [s for s in seg if s.startswith('info depth ')]
            m = INFO_RX.match(last[-1]) if last else None
            row = f'{j}\t{m.group(1)}\t{m.group(2)}\t{m.group(3)}\t{line.split()[1]}' if m else f'{j}\t?'
            r.det.append(row)
            if row == ref_rows[j]:
                same += 1
            elif len([f for f in r.fails if f.startswith('tail')]) < 3:
                r.fail(f'tail FEN {j}: got [{row}] want [{ref_rows[j]}]')
        r.notes.append(f'Threads 1 tail {same} / {len(fens50)} = lock L3 reference')
        if same != len(fens50):
            r.fail(f'Threads 1 tail {same} / {len(fens50)} identical')
        e.send('bench 13')
        _, b = e.until(lambda s: 'bench depth' in s, 600, 'bench 13')
        if f'nodes {PIN13}' not in b:
            r.fail(f'bench 13 not {PIN13}: {b}')
    return script


# ---------------------------------------------------------------- 1e extreme
def load_extreme():
    rows = []
    for l in open(DATA / 'extreme_fens.tsv', encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            f = l.rstrip('\n').split('\t')
            rows.append({'id': f[0], 'set': f[1], 'fen': f[2], 'expect': f[5]})
    return rows


def extreme_script(rows, depth, perft):
    acc = [x for x in rows if x['set'] == 'A']
    rej = [x for x in rows if x['set'] == 'R']
    base = next(x for x in acc if x['id'] == 'A10')

    def script(e, r):
        uci_init(e, ['setoption name OwnBook value false'])
        r.perft = []
        for x in acc:
            e.send('ucinewgame')
            e.sync()
            e.send('position fen ' + x['fen'])
            mark = len(e.log)
            line, seg = e.search(f'go depth {depth}', 1800)
            if any('invalid' in s for s in seg if s.startswith('info string')):
                r.fail(f'{x["id"]}: rejected by the engine')
            ok, det = legal(x['fen'], [], line)
            if not ok:
                r.fail(f'{x["id"]}: {det}')
            e.send(f'go perft {perft}')
            _, nl = e.until(lambda s: s.startswith('nodes '), 1800, f'{x["id"]} perft')
            block = [s for s in e.log[mark:] if re.match(r'^[a-h][1-8][a-h][1-8][qrbn]?: \d+$', s)] + [nl]
            r.perft.append((x['id'], block))
            exp = x['expect']
            if exp.startswith('perft3=') and perft == 3 and nl != 'nodes ' + exp.split('=')[1]:
                r.fail(f'{x["id"]}: {nl}, published perft 3 = {exp.split("=")[1]}')
            if exp.startswith('moves=') and len(block) - 1 != int(exp.split('=')[1]):
                r.fail(f'{x["id"]}: {len(block) - 1} root moves, want {exp.split("=")[1]}')
        e.send('ucinewgame')
        e.send('position fen ' + base['fen'])
        e.sync()
        e.send('go perft 1')
        _, n0 = e.until(lambda s: s.startswith('nodes '), 60, 'base perft 1')
        for x in rej:
            e.send('position fen ' + x['fen'])
            got = [s for s in e.collect_sync(60) if s.startswith('info string')]
            want = 'info string invalid FEN: ' + x['expect']
            if got != [want]:
                r.fail(f'{x["id"]}: got {got}, want [{want}]')
            e.send('go perft 1')
            _, n1 = e.until(lambda s: s.startswith('nodes '), 60, f'{x["id"]} perft 1')
            if n1 != n0:
                r.fail(f'{x["id"]}: position not kept ({n1} after the rejected FEN, {n0} before)')
    return script


# ---------------------------------------------------------------- driver
def main():
    ap = argparse.ArgumentParser(description='patch review QA tests 1a-1e (see the module docstring)')
    ap.add_argument('test', choices=['replay', 'protocol', 'soak', 'extreme'])
    ap.add_argument('--out', required=True)
    ap.add_argument('--mask', default='0xC')
    ap.add_argument('--stacks', default=','.join(STACKS))
    ap.add_argument('--pgn', default='F:/forge_push/gate_stB_lmrcapvictim1_vs_AL1/gate_stB_lmrcapvictim1_vs_AL1.pgn')
    ap.add_argument('--game', type=int, default=379)
    ap.add_argument('--depth', type=int, default=0)
    ap.add_argument('--movetime', type=int, default=300)
    ap.add_argument('--ref-tsv', default='F:/ospd/ref/fd3a5190/fens_e7dbf2c8_n2000_d13_ob0.tsv')
    ap.add_argument('--mutex-wait-min', type=float, default=240.0,
                    help='minutes to wait for the timing mutex when --mask touches CPUs 2-3 (0 = refuse at once)')
    a = ap.parse_args()
    mask = int(a.mask, 0)
    if a.test == 'soak' and mask != 0xF:
        raise SystemExit('soak runs on CPUs 0-3: --mask 0xF (held under the timing mutex)')
    stacks = [s for s in a.stacks.split(',') if s]
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    head = [f'# patchrev_qa.py {a.test} {time.strftime("%Y-%m-%d %H:%M:%S")}', '# ' + place(mask)]
    # CPUs 2-3 only under abba.ps1's timing mutex (released at exit); refused before any engine or exe check
    atexit.register(hold_timing_mutex(mask, a.mutex_wait_min))
    head.append('# timing mutex ' + TIMING_MUTEX + (': held for this run (mask touches CPUs 2-3)' if mask & TIMING_CPUS
                                                    else ': not needed (mask inside 0x3)'))
    if sha256(LOCK) != LOCK_SHA:
        raise SystemExit(f'{LOCK} is not the lock FD3A5190')
    exes = [('lock', LOCK, None)] + [(s, kit_exe(s), None) for s in stacks]
    results, refs = [], {}
    if a.test == 'replay':
        moves, ngames, res = load_game(a.pgn, a.game)
        depth = a.depth or 10
        head.append(f'# game {a.game} of {ngames} in {a.pgn} (md5 {md5(a.pgn)}), {len(moves)} plies, result {res}, '
                    f'go depth {depth}, 2 passes, option changes every 10 plies in pass 2')
        script = replay_script(moves, depth, 10)
        exes = exes + [('lock_again', LOCK, None)]
    elif a.test == 'protocol':
        fens20 = game_rows(0, 20)
        head.append('# 20 movetime positions = data/game_positions_300.tsv rows 0-19; mate FENs ' + M3 + ' | ' + M1)
        script = protocol_script(fens20)
    elif a.test == 'soak':
        pos60 = game_rows(20, 80)
        fens50 = [l.strip() for l in open(DATA / 'fens_12k_v2.txt', encoding='utf-8') if l.strip() and not l.startswith('#')][:50]
        ref_rows = [l.rstrip('\n') for l in open(a.ref_tsv, encoding='utf-8')][:50]
        head.append(f'# soak: game_positions_300 rows 20-79 x go movetime {a.movetime}, Threads 2/3/4, Hash {HASHES}; '
                    f'tail fens_12k_v2 rows 0-49 go depth 13 vs {a.ref_tsv} (md5 {md5(a.ref_tsv)}); SOAK ONLY, not a lock proof')
        script = soak_script(pos60, fens50, ref_rows, a.movetime)
    else:
        rows = load_extreme()
        depth = a.depth or 8
        head.append(f'# extreme: data/extreme_fens.tsv (md5 {md5(DATA / "extreme_fens.tsv")}), {len(rows)} FENs, '
                    f'go depth {depth} + go perft 3 (set A), rejection + kept position (set R)')
        script = extreme_script(rows, depth, 3)
        env = msvc_env()
        exes = exes + [(f'{s}_ubsan', f'{san_dir(s)}/forge_ubsan_trap.exe', None) for s in stacks]
        exes = exes + [('lock_asan', LOCK_ASAN, env)] + [(f'{s}_asan', f'{san_dir(s)}/forge_asan_msvc.exe', env) for s in stacks]
    for name, exe, env in exes:
        if not os.path.isfile(exe):
            raise SystemExit(f'missing exe {exe}')
        head.append(f'# {name} {exe} sha256 {sha256(exe)[:16]}')
    for name, exe, env in exes:
        t0 = time.perf_counter()
        r = run_one(name, exe, out, script, env)
        r.secs = time.perf_counter() - t0
        results.append(r)
        print(f'{name}: {r.verdict} {r.secs:.0f} s {"; ".join(r.fails[:3])}', flush=True)
    # comparisons against the lock run of the same group
    ref = {'g': next(r for r in results if r.name == 'lock')}
    if a.test == 'extreme':
        ref['m'] = next(r for r in results if r.name == 'lock_asan')
    for r in results:
        grp = 'm' if r.name.endswith('_asan') else 'g'
        base = ref[grp]
        if r is base:
            continue
        if a.test in ('protocol', 'soak'):
            # timed searches (and Threads > 1) are not reproducible: only the deterministic parts are compared
            # (protocol: S4-S6 after ucinewgame; soak: the Threads 1 tail rows, also checked against the L3 reference)
            d = first_diff(base.det, r.det)
            if d is not None:
                r.fail(f'deterministic part differs from the lock at line {d}: {r.det[d] if d < len(r.det) else "<end>"}')
        else:
            na, nb = norm(base.log), norm(r.log)
            d = first_diff(na, nb)
            if d is not None:
                r.fail(f'transcript differs from {base.name} at normalised line {d}: '
                       f'[{na[d] if d < len(na) else "<end>"}] vs [{nb[d] if d < len(nb) else "<end>"}]')
    if a.test == 'extreme' and ref['g'].perft != ref['m'].perft:
        ref['m'].fail('perft blocks of the MSVC group differ from the g++ group')
    tsv = ['name\texe\tsha256\tverdict\texit\tsecs\tnormalised_lines\tnotes\tfailures']
    for r in results:
        tsv.append('\t'.join([r.name, r.exe, sha256(r.exe)[:16], r.verdict, str(r.rc), f'{r.secs:.0f}',
                              str(len(norm(r.log))), '; '.join(r.notes), '; '.join(r.fails)]))
    write(out / 'results.tsv', head + tsv)
    nfail = sum(1 for r in results if r.verdict != 'PASS')
    summary = (f'{a.test}: {len(results) - nfail} / {len(results)} PASS ' +
               ' '.join(f'{r.name}={r.verdict}' for r in results))
    write(out / 'summary.txt', head + [summary])
    print(summary)
    return 3 if nfail else 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - report and exit 1
        print('ERROR:', type(exc).__name__, exc)
        sys.exit(1)
