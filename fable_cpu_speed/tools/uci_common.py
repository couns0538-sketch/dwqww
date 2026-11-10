# uci_common.py - shared helpers of the fable4cpu harness scripts (Python standard library only).
# Every child process is created while this process is itself restricted to the child's mask, so the child
# is pinned from its first instruction; the mask is read back from the child and must match.
import ctypes
import ctypes.wintypes as wt
import datetime
import hashlib
import os
import queue
import shutil
import subprocess
import sys
import threading
import time

JOB = r'D:\forge_jobs_20261110\fable4cpu'
REPO = JOB + r'\repo'
LOGS = REPO + r'\fable_cpu_speed\evidence\logs'
LOCK_EXE = JOB + r'\out\base\combo29_lock.exe'
LOCK_MD5 = 'c0051c99695f48bf93272d96fe7548c3'
LOCK_SHA256 = 'e1284f7fc492c8fe1285797fdae8988cf2f2926b33fcfee7023d284d67d8802e'
SOURCE_REV = '16833ecc03b425586f91f4c8834dea8807bf4c22'
CORPUS = REPO + r'\fable_cpu_speed\tests\fens_12k_v2.txt'
LANE = 0x707F
# The PC's UTC clock runs this many seconds ahead of github.com's Date header (measured once, at the clone).
PC_UTC_AHEAD_S = 25159.3
BELOW_NORMAL = 0x00004000
KIWIPETE = 'r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1'

_k32 = ctypes.WinDLL('kernel32', use_last_error=True)
_k32.GetCurrentProcess.restype = wt.HANDLE
_k32.GetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
_k32.GetProcessAffinityMask.restype = wt.BOOL
_k32.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
_k32.SetProcessAffinityMask.restype = wt.BOOL
_k32.QueryProcessCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
_k32.QueryProcessCycleTime.restype = wt.BOOL
_k32.GetProcessTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(wt.FILETIME)] * 4
_k32.GetProcessTimes.restype = wt.BOOL


class EngineError(Exception):
    pass


def vienna_now():
    t = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    t = t - datetime.timedelta(seconds=PC_UTC_AHEAD_S) + datetime.timedelta(hours=1)
    return t.strftime('%Y-%m-%d %H:%M:%S') + ' Vienna'


def hashes(path):
    m = hashlib.md5()
    s = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            m.update(chunk)
            s.update(chunk)
    return m.hexdigest(), s.hexdigest()


def affinity_of(handle):
    pm = ctypes.c_size_t()
    sm = ctypes.c_size_t()
    if not _k32.GetProcessAffinityMask(handle, ctypes.byref(pm), ctypes.byref(sm)):
        return 0
    return pm.value


def self_affinity():
    return affinity_of(_k32.GetCurrentProcess())


def require_lane():
    m = self_affinity()
    if m == 0 or (m & ~LANE):
        raise SystemExit('refusing: this process is not pinned inside 0x707F (mask 0x%X)' % m)
    return m


def parse_mask(text):
    m = int(text, 0)
    if m <= 0 or (m & ~LANE):
        raise SystemExit('mask %s is not inside 0x707F' % text)
    return m


def disk_free_gib():
    return shutil.disk_usage('D:\\').free / (1 << 30)


def disk_guard(min_gib=31.0):
    f = disk_free_gib()
    if f < min_gib:
        raise SystemExit('NOT STARTED (disk guard): D: has %.2f GiB free, under %.1f' % (f, min_gib))
    return f


_spawn_lock = threading.Lock()


def spawn(args, mask, **kw):
    """Start a child restricted to `mask` (inside the lane) from its first instruction; verify by read-back."""
    if mask <= 0 or (mask & ~LANE):
        raise ValueError('mask 0x%X is not inside 0x707F' % mask)
    kw.setdefault('creationflags', BELOW_NORMAL)
    with _spawn_lock:
        me = _k32.GetCurrentProcess()
        prev = self_affinity()
        if not _k32.SetProcessAffinityMask(me, mask):
            raise OSError('cannot set own affinity to 0x%X' % mask)
        try:
            p = subprocess.Popen(args, **kw)
        finally:
            _k32.SetProcessAffinityMask(me, prev)
    got = affinity_of(int(p._handle))
    if got != mask:
        p.kill()
        raise RuntimeError('child affinity 0x%X is not the requested 0x%X' % (got, mask))
    return p


def cycles_of(handle):
    c = ctypes.c_uint64()
    if not _k32.QueryProcessCycleTime(handle, ctypes.byref(c)):
        return 0
    return c.value


def cpu_seconds_of(handle):
    ft = [wt.FILETIME() for _ in range(4)]
    if not _k32.GetProcessTimes(handle, *[ctypes.byref(x) for x in ft]):
        return 0.0
    k = (ft[2].dwHighDateTime << 32) | ft[2].dwLowDateTime
    u = (ft[3].dwHighDateTime << 32) | ft[3].dwLowDateTime
    return (k + u) / 1e7


def header(title, scripts, exes=(), extra=()):
    """First lines of every evidence log: time, script hashes, exe hashes, own placement."""
    out = ['%s; %s' % (title, vienna_now())]
    for s in scripts:
        out.append('script %s sha256 %s' % (os.path.basename(s), hashes(s)[1]))
    out.append('python %s; this process mask 0x%X; source revision %s' % (sys.version.split()[0], self_affinity(), SOURCE_REV))
    for e in exes:
        md5, sha = hashes(e)
        out.append('exe %s bytes %d md5 %s sha256 %s' % (e, os.path.getsize(e), md5, sha))
    out.extend(extra)
    return out


def read_fens(first=1, count=None, path=CORPUS):
    with open(path, 'r', encoding='ascii') as f:
        fens = [x.strip() for x in f if x.strip()]
    sel = fens[first - 1:] if count is None else fens[first - 1:first - 1 + count]
    return sel


class Engine:
    """One UCI engine process, pinned to `mask`. Output ending, a timeout or a broken pipe raise EngineError."""

    def __init__(self, exe, mask, errfile=None, env=None, transcript=None):
        self.exe = exe
        self.mask = mask
        self._err = open(errfile, 'ab') if errfile else subprocess.DEVNULL
        self._tr = open(transcript, 'a', encoding='ascii', errors='replace') if transcript else None
        self.p = spawn([exe], mask, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._err, env=env,
                       cwd=os.path.dirname(exe))
        self.child_mask = affinity_of(int(self.p._handle))
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._rd, daemon=True)
        self.t.start()

    def _rd(self):
        try:
            for raw in self.p.stdout:
                self.q.put(raw.decode('ascii', 'replace').rstrip('\r\n'))
        finally:
            self.q.put(None)

    def send(self, s):
        if self._tr:
            self._tr.write('> ' + s + '\n')
        try:
            self.p.stdin.write((s + '\n').encode('ascii'))
            self.p.stdin.flush()
        except OSError as e:
            raise EngineError('cannot write to engine (exit %s): %s' % (self.p.poll(), e))

    def read_until(self, pred, timeout):
        end = time.monotonic() + timeout
        got = []
        while True:
            left = end - time.monotonic()
            if left <= 0:
                raise EngineError('timeout after %.0f s' % timeout)
            try:
                line = self.q.get(timeout=left)
            except queue.Empty:
                raise EngineError('timeout after %.0f s' % timeout)
            if line is None:
                raise EngineError('engine output ended (exit %s)' % self.p.poll())
            if self._tr:
                self._tr.write(line + '\n')
            got.append(line)
            if pred(line):
                return got

    def uci(self, timeout=60):
        self.send('uci')
        return self.read_until(lambda l: l == 'uciok', timeout)

    def isready(self, timeout=120):
        self.send('isready')
        self.read_until(lambda l: l == 'readyok', timeout)

    def setoption(self, name, value=None):
        self.send('setoption name %s' % name if value is None else 'setoption name %s value %s' % (name, value))

    def bench(self, depth, timeout):
        self.send('bench %d' % depth)
        lines = self.read_until(lambda l: l.startswith('info string bench depth'), timeout)
        tok = lines[-1].split()
        if int(tok[tok.index('depth') + 1]) != depth:
            raise EngineError('bench line reports another depth: ' + lines[-1])
        return int(tok[tok.index('nodes') + 1]), int(tok[tok.index('time') + 1])

    def perft(self, depth, timeout):
        self.send('go perft %d' % depth)
        lines = self.read_until(lambda l: l.startswith('nodes '), timeout)
        return int(lines[-1].split()[1]), lines[:-1]

    def go(self, limit, timeout):
        """Returns (depth, score text, nodes, bestmove) from the last info line with a score and the bestmove line."""
        self.send('go ' + limit)
        lines = self.read_until(lambda l: l.startswith('bestmove'), timeout)
        best = lines[-1].split()[1] if len(lines[-1].split()) > 1 else '?'
        depth, score, nodes = -1, '?', -1
        for l in reversed(lines):
            if l.startswith('info depth ') and ' score ' in l and ' nodes ' in l:
                tok = l.split()
                depth = int(tok[tok.index('depth') + 1])
                i = tok.index('score')
                score = tok[i + 1] + ' ' + tok[i + 2]
                nodes = int(tok[tok.index('nodes') + 1])
                break
        return depth, score, nodes, best

    def quit(self, timeout=60):
        """Sends quit and returns the exit code; a hang is an EngineError (the child, which is mine, is ended)."""
        try:
            self.send('quit')
        except EngineError:
            pass
        try:
            code = self.p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.kill()
            raise EngineError('engine did not exit within %.0f s after quit' % timeout)
        self._close_files()
        return code

    def kill(self):
        try:
            self.p.kill()
            self.p.wait(timeout=30)
        except Exception:  # noqa
            pass
        self._close_files()

    def _close_files(self):
        for f in (self._tr, self._err):
            try:
                if f not in (None, subprocess.DEVNULL):
                    f.close()
            except Exception:  # noqa
                pass


def write_log(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='ascii', errors='replace', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
