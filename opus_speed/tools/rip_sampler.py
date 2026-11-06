"""rip_sampler.py - flat sampling profile of one Forge engine process (speed hunt 2026-11-05, own code).

usage: python -I -B rip_sampler.py <exe> <new out dir> [--bench 20] [--repeat 3] [--rate 1000]
                                   [--self-mask 0x3] [--engine-mask 0x2] [--nm C:/msys64/ucrt64/bin/nm.exe]

What it does
- Pins ITSELF first (affinity --self-mask, Idle class), reads both back and fails closed; the engine inherits the Idle
  class and is then narrowed to --engine-mask (a subset of the own mask); both values are read back on the engine too.
- Drives the engine over UCI (uci / isready / 'bench D' --repeat times, waits for each 'bench depth D nodes' line).
- While a bench runs it samples the busiest engine thread: SuspendThread -> GetThreadContext(CONTEXT_CONTROL) ->
  ResumeThread (always, in a finally block), about --rate times per second (timeBeginPeriod(1) + sleep).
- Rebases every RIP by the engine's runtime module base (the exe has DYNAMIC_BASE) to the exe's own VMA
  (rip - base + ImageBase) and maps it to the nearest preceding text symbol of `nm -n` (the kit exes keep their symbol
  table). Samples outside .text are counted as 'outside' (system DLLs, kernel); a run with < 90 % inside fails.
- Never kills: the engine gets 'quit', then EOF; a survivor is reported, not ended.
Outputs (out dir must not exist): meta.json, functions.tsv (symbol, samples, %), addresses.tsv (rebased hex VMA,
samples), profile.txt (top 40 functions + the 12 hottest addresses of each of the top 8), uci.log.
"""
import argparse
import bisect
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
import pathlib
import queue
import re
import struct
import subprocess
import sys
import threading
import time

K32 = ctypes.WinDLL('kernel32', use_last_error=True)
WINMM = ctypes.WinDLL('winmm')

IDLE_PRIORITY_CLASS = 0x40
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_SET_INFORMATION = 0x0200
THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
TH32CS_SNAPTHREAD = 0x4
CONTEXT_AMD64 = 0x00100000
CONTEXT_CONTROL = CONTEXT_AMD64 | 0x1
CONTEXT_SIZE = 1232          # sizeof(CONTEXT) on x64
OFF_FLAGS = 0x30             # CONTEXT.ContextFlags
OFF_RIP = 0xF8               # CONTEXT.Rip (validated at run time: rebased samples must land in .text)


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ThreadID', wt.DWORD),
                ('th32OwnerProcessID', wt.DWORD), ('tpBasePri', wt.LONG), ('tpDeltaPri', wt.LONG),
                ('dwFlags', wt.DWORD)]


class FILETIME(ctypes.Structure):
    _fields_ = [('lo', wt.DWORD), ('hi', wt.DWORD)]


K32.OpenProcess.restype = wt.HANDLE
K32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
K32.OpenThread.restype = wt.HANDLE
K32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
K32.CloseHandle.argtypes = [wt.HANDLE]
K32.GetCurrentProcess.restype = wt.HANDLE
K32.SetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.c_size_t]
K32.GetProcessAffinityMask.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
K32.SetPriorityClass.argtypes = [wt.HANDLE, wt.DWORD]
K32.GetPriorityClass.argtypes = [wt.HANDLE]
K32.GetPriorityClass.restype = wt.DWORD
K32.CreateToolhelp32Snapshot.restype = wt.HANDLE
K32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
K32.Thread32First.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
K32.Thread32Next.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
K32.SuspendThread.argtypes = [wt.HANDLE]
K32.SuspendThread.restype = wt.DWORD
K32.ResumeThread.argtypes = [wt.HANDLE]
K32.ResumeThread.restype = wt.DWORD
K32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
K32.GetThreadTimes.argtypes = [wt.HANDLE] + [ctypes.POINTER(FILETIME)] * 4
K32.K32EnumProcessModules.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_void_p), wt.DWORD, ctypes.POINTER(wt.DWORD)]


def fail(msg):
    print('rip_sampler: FAIL ' + msg)
    sys.exit(1)


def place_self(mask):
    me = K32.GetCurrentProcess()
    if mask <= 0 or mask & ~0xF:
        fail('self mask 0x%X is outside CPUs 0-3' % mask)
    if not K32.SetPriorityClass(me, IDLE_PRIORITY_CLASS) or not K32.SetProcessAffinityMask(me, mask):
        fail('could not set own placement (error %d)' % ctypes.get_last_error())
    return read_placement(me)


def read_placement(handle):
    pm, sm = ctypes.c_size_t(), ctypes.c_size_t()
    if not K32.GetProcessAffinityMask(handle, ctypes.byref(pm), ctypes.byref(sm)):
        fail('GetProcessAffinityMask error %d' % ctypes.get_last_error())
    return pm.value, K32.GetPriorityClass(handle)


def pe_info(exe):
    data = pathlib.Path(exe).read_bytes()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, pe + 6)[0]
    opt = pe + 24
    optsize = struct.unpack_from('<H', data, pe + 20)[0]
    image_base = struct.unpack_from('<Q', data, opt + 24)[0]
    text = None
    for i in range(nsec):
        s = opt + optsize + 40 * i
        name = data[s:s + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, vaddr = struct.unpack_from('<II', data, s + 8)
        if name == '.text':
            text = (image_base + vaddr, image_base + vaddr + vsize)
    if text is None:
        fail('no .text section in ' + exe)
    return image_base, text, hashlib.sha256(data).hexdigest()


def load_symbols(exe, nm):
    out = subprocess.run([nm, '-n', '--defined-only', '-C', exe], capture_output=True, text=True, errors='replace')
    if out.returncode != 0:
        fail('nm failed: ' + out.stderr[:300])
    addrs, names = [], []
    for line in out.stdout.splitlines():
        m = re.match(r'^([0-9a-fA-F]{8,16}) ([tTwW]) (.*)$', line)
        if not m:
            continue
        a = int(m.group(1), 16)
        name = m.group(3)
        if addrs and addrs[-1] == a:
            # several names at one address: a section label ('.text.hot', '.text$x') shares the address of the first
            # function in its section (found 2026-11-05: generate_pseudo_legal / static_evaluate showed as '.text.hot')
            if names[-1].startswith('.') and not name.startswith('.'):
                names[-1] = name
            continue
        addrs.append(a)
        names.append(name)
    if len(addrs) < 100:
        fail('only %d text symbols from nm' % len(addrs))
    return addrs, names


def engine_threads(pid):
    snap = K32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap in (None, wt.HANDLE(-1).value):
        fail('thread snapshot failed')
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(THREADENTRY32)
    tids = []
    ok = K32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            tids.append(te.th32ThreadID)
        ok = K32.Thread32Next(snap, ctypes.byref(te))
    K32.CloseHandle(snap)
    return tids


def user_time(h):
    c, e, k, u = FILETIME(), FILETIME(), FILETIME(), FILETIME()
    if not K32.GetThreadTimes(h, ctypes.byref(c), ctypes.byref(e), ctypes.byref(k), ctypes.byref(u)):
        return 0
    return (u.hi << 32) | u.lo


def module_base(hproc):
    mods = (ctypes.c_void_p * 64)()
    need = wt.DWORD()
    if not K32.K32EnumProcessModules(hproc, mods, ctypes.sizeof(mods), ctypes.byref(need)) or not mods[0]:
        fail('EnumProcessModules error %d' % ctypes.get_last_error())
    return mods[0]


class Engine:
    def __init__(self, exe, log):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  cwd=os.path.dirname(exe) or None, text=True, bufsize=1)
        self.q = queue.Queue()
        self.log = log
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        for line in self.p.stdout:
            self.q.put(line.rstrip('\r\n'))
        self.q.put(None)

    def send(self, line):
        self.log.write('> ' + line + '\n')
        self.p.stdin.write(line + '\n')
        self.p.stdin.flush()

    def wait_for(self, pattern, timeout, on_tick=None):
        rx = re.compile(pattern)
        deadline = time.perf_counter() + timeout
        while True:
            left = deadline - time.perf_counter()
            if left <= 0:
                raise TimeoutError('no /%s/ within %d s' % (pattern, timeout))
            try:
                # with a sampler callback: poll without blocking, so sampling runs nearly all the time
                line = self.q.get_nowait() if on_tick else self.q.get(timeout=left)
            except queue.Empty:
                if on_tick:
                    on_tick()
                continue
            if line is None:
                raise EOFError('engine exited before /%s/' % pattern)
            self.log.write(line + '\n')
            m = rx.search(line)
            if m:
                return m

    def stop(self):
        try:
            self.send('quit')
            self.p.stdin.close()
        except OSError:
            pass
        try:
            self.p.wait(30)
            return True
        except subprocess.TimeoutExpired:
            return False


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == '--remap':
        return remap(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'C:/msys64/ucrt64/bin/nm.exe')
    ap = argparse.ArgumentParser()
    ap.add_argument('exe')
    ap.add_argument('out')
    ap.add_argument('--bench', type=int, default=20)
    ap.add_argument('--repeat', type=int, default=3)
    ap.add_argument('--rate', type=int, default=1000)
    ap.add_argument('--self-mask', type=lambda s: int(s, 0), default=0x3)
    ap.add_argument('--engine-mask', type=lambda s: int(s, 0), default=0x2)
    ap.add_argument('--nm', default='C:/msys64/ucrt64/bin/nm.exe')
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    if out.exists():
        fail('%s exists' % out)
    mask, cls = place_self(a.self_mask)
    if mask != a.self_mask or cls != IDLE_PRIORITY_CLASS:
        fail('own placement read back 0x%X / class 0x%X' % (mask, cls))
    if a.engine_mask & ~a.self_mask or a.engine_mask == 0:
        fail('engine mask must be a non-empty subset of the own mask')
    image_base, (text_lo, text_hi), sha = pe_info(a.exe)
    addrs, names = load_symbols(a.exe, a.nm)
    out.mkdir(parents=True)
    log = open(out / 'uci.log', 'w', encoding='utf-8', newline='\n')
    eng = Engine(a.exe, log)
    hproc = K32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_SET_INFORMATION, False, eng.p.pid)
    if not hproc:
        fail('OpenProcess error %d' % ctypes.get_last_error())
    if not K32.SetProcessAffinityMask(hproc, a.engine_mask):
        fail('could not narrow the engine mask')
    emask, ecls = read_placement(hproc)
    if emask != a.engine_mask or ecls != IDLE_PRIORITY_CLASS:
        eng.stop()
        fail('engine placement read back 0x%X / class 0x%X - refused' % (emask, ecls))
    counts = {}
    total = outside = failed = 0
    benches = []
    WINMM.timeBeginPeriod(1)
    raw = ctypes.create_string_buffer(CONTEXT_SIZE + 16)
    ctx = (ctypes.addressof(raw) + 15) & ~15
    try:
        eng.send('uci')
        eng.wait_for(r'^uciok', 60)
        eng.send('isready')
        eng.wait_for(r'^readyok', 60)
        base = module_base(hproc)
        delta = image_base - base
        for rep in range(a.repeat):
            eng.send('bench %d' % a.bench)
            # pick the busiest thread over a short window after the bench started
            time.sleep(0.3)
            handles = {}
            for tid in engine_threads(eng.p.pid):
                h = K32.OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, False, tid)
                if h:
                    handles[tid] = h
            t0 = {tid: user_time(h) for tid, h in handles.items()}
            time.sleep(0.2)
            busy = max(handles, key=lambda tid: user_time(handles[tid]) - t0[tid])
            h = handles[busy]
            state = {'n': 0}

            def tick():
                # sample a few times per 50 ms queue poll; each sample suspends for a few microseconds
                end = time.perf_counter() + 0.045
                while time.perf_counter() < end:
                    nonlocal_sample()
                    time.sleep(1.0 / a.rate)

            def nonlocal_sample():
                nonlocal total, outside, failed
                if K32.SuspendThread(h) == 0xFFFFFFFF:
                    failed += 1
                    return
                try:
                    ctypes.c_uint32.from_address(ctx + OFF_FLAGS).value = CONTEXT_CONTROL
                    ok = K32.GetThreadContext(h, ctypes.c_void_p(ctx))
                    rip = ctypes.c_uint64.from_address(ctx + OFF_RIP).value if ok else 0
                finally:
                    K32.ResumeThread(h)
                if not ok:
                    failed += 1
                    return
                total += 1
                v = rip + delta
                if text_lo <= v < text_hi:
                    counts[v] = counts.get(v, 0) + 1
                else:
                    outside += 1

            m = eng.wait_for(r'bench depth %d nodes (\d+) time (\d+) nps (\d+)' % a.bench, 3600, on_tick=tick)
            benches.append({'nodes': int(m.group(1)), 'ms': int(m.group(2)), 'nps': int(m.group(3)), 'thread': busy})
            for hh in handles.values():
                K32.CloseHandle(hh)
    finally:
        WINMM.timeEndPeriod(1)
        exited = eng.stop()
        log.close()
    inside = total - outside
    if total == 0 or inside < 0.9 * total:
        fail('only %d of %d samples inside .text (context layout or rebase wrong?)' % (inside, total))
    with open(out / 'addresses.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write('vma\tsamples\n')
        for v, c in sorted(counts.items()):
            f.write('%x\t%d\n' % (v, c))
    head = ['exe %s sha256 %s' % (a.exe, sha),
            'bench %d x %d: %s' % (a.bench, a.repeat, ', '.join('%d nodes %d ms %d nps' % (b['nodes'], b['ms'], b['nps']) for b in benches)),
            'samples %d, inside .text %d (%.1f %%), outside %d, failed %d; self mask 0x%X Idle, engine mask 0x%X Idle'
            % (total, inside, 100.0 * inside / total, outside, failed, a.self_mask, a.engine_mask)]
    meta = {'exe': a.exe, 'sha256': sha, 'bench': a.bench, 'repeat': a.repeat, 'benches': benches, 'samples': total,
            'inside': inside, 'outside': outside, 'failed': failed, 'image_base': hex(image_base),
            'text': [hex(text_lo), hex(text_hi)], 'self_mask': a.self_mask, 'engine_mask': a.engine_mask,
            'engine_exited': exited, 'head': head}
    (out / 'meta.json').write_text(json.dumps(meta, indent=1) + '\n', encoding='utf-8', newline='\n')
    lines = report(out, counts, addrs, names, inside, head, '')
    print('\n'.join(lines[:3 + 25]))
    if not exited:
        print('rip_sampler: WARNING engine pid %d did not exit (left running, no-kill rule)' % eng.p.pid)
    return 0


def report(out, counts, addrs, names, inside, head, suffix):
    """functions<suffix>.tsv + profile<suffix>.txt from {rebased vma: samples}; returns the profile lines."""
    func = {}
    for v, c in counts.items():
        i = bisect.bisect_right(addrs, v) - 1
        name = names[i] if i >= 0 else '?'
        func.setdefault(name, [0, {}])
        func[name][0] += c
        func[name][1][v] = c
    ranked = sorted(func.items(), key=lambda kv: -kv[1][0])
    with open(out / ('functions%s.tsv' % suffix), 'w', encoding='utf-8', newline='\n') as f:
        f.write('samples\tpct\tsymbol\n')
        for name, (c, _) in ranked:
            f.write('%d\t%.2f\t%s\n' % (c, 100.0 * c / inside, name))
    lines = list(head) + ['', 'top functions (self samples, % of inside):']
    for name, (c, _) in ranked[:40]:
        lines.append('%7d %6.2f%%  %s' % (c, 100.0 * c / inside, name[:150]))
    lines.append('')
    for name, (c, per) in ranked[:8]:
        lines.append('hottest addresses in %s:' % name[:120])
        for v, cc in sorted(per.items(), key=lambda kv: -kv[1])[:12]:
            lines.append('   %x %6d %5.2f%%' % (v, cc, 100.0 * cc / inside))
    (out / ('profile%s.txt' % suffix)).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    return lines


def remap(run_dir, nm):
    """Re-attribute a finished run (its addresses.tsv) with the current symbol rules; writes *_remap files."""
    run = pathlib.Path(run_dir)
    meta = json.loads((run / 'meta.json').read_text(encoding='utf-8'))
    _, _, sha = pe_info(meta['exe'])
    if sha != meta['sha256']:
        fail('exe %s changed since the run (sha256 %s, run %s)' % (meta['exe'], sha, meta['sha256']))
    addrs, names = load_symbols(meta['exe'], nm)
    counts = {}
    for line in (run / 'addresses.tsv').read_text(encoding='utf-8').splitlines()[1:]:
        v, c = line.split('\t')
        counts[int(v, 16)] = int(c)
    head = meta.get('head') or ['exe %s sha256 %s (remapped run %s)' % (meta['exe'], sha, run)]
    lines = report(run, counts, addrs, names, meta['inside'], head, '_remap')
    print('\n'.join(lines[:3 + 25]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
