r"""rip_sampler.py - self-time profile of one `bench N` of a Forge exe (standard library only, own code).

Method ("user-mode instruction-pointer sampling"): the engine runs as a pinned child; while the bench runs, the
instruction pointer of its threads is read (SuspendThread / GetThreadContext / ResumeThread). A sample is taken
only when the thread's own CPU-cycle counter (QueryThreadCycleTime) has advanced by at least --quantum cycles
since its last sample, so a preempted thread is not counted again at the same address. Only this job's own child
is ever suspended, for microseconds, and always resumed.

Addresses are stored relative to the image base and resolved with llvm-symbolizer --inlines against the build's
PDB (through a copy of the exe without the DWARF sections of the static runtime libraries, same addresses).

Every sample goes to exactly one category, so the shares add to 100 %:
  walk the frames from the innermost outwards and stop at the first frame that names a listed function or that
  was written in one of the engine's .cpp files; helper code inlined from headers (standard library, bit helpers,
  accessors) is thereby charged to the function it was inlined into. Samples outside the engine image or without
  a resolved frame are "other".

usage: rip_sampler.py --exe X --out DIR --log L --mask 0x1000 [--depth 22] [--net on|off] [--quantum 1500000] [--repeat 2]
"""
import argparse
import collections
import ctypes
import ctypes.wintypes as wt
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

LLVM = r'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'
k32 = ctypes.WinDLL('kernel32', use_last_error=True)
psapi = ctypes.WinDLL('psapi', use_last_error=True)
TH32CS_SNAPTHREAD = 0x00000004
THREAD_ACCESS = 0x0002 | 0x0008 | 0x0040          # SUSPEND_RESUME | GET_CONTEXT | QUERY_INFORMATION
CONTEXT_CONTROL = 0x00100001
CONTEXT_SIZE = 1232
OFF_FLAGS = 0x30
OFF_RIP = 0xF8


class THREADENTRY32(ctypes.Structure):
    _fields_ = [('dwSize', wt.DWORD), ('cntUsage', wt.DWORD), ('th32ThreadID', wt.DWORD),
                ('th32OwnerProcessID', wt.DWORD), ('tpBasePri', wt.LONG), ('tpDeltaPri', wt.LONG),
                ('dwFlags', wt.DWORD)]


class MODULEINFO(ctypes.Structure):
    _fields_ = [('lpBaseOfDll', ctypes.c_void_p), ('SizeOfImage', wt.DWORD), ('EntryPoint', ctypes.c_void_p)]


k32.CreateToolhelp32Snapshot.restype = wt.HANDLE
k32.CreateToolhelp32Snapshot.argtypes = [wt.DWORD, wt.DWORD]
k32.Thread32First.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
k32.Thread32Next.argtypes = [wt.HANDLE, ctypes.POINTER(THREADENTRY32)]
k32.OpenThread.restype = wt.HANDLE
k32.OpenThread.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.CloseHandle.argtypes = [wt.HANDLE]
k32.SuspendThread.argtypes = [wt.HANDLE]
k32.SuspendThread.restype = wt.DWORD
k32.ResumeThread.argtypes = [wt.HANDLE]
k32.ResumeThread.restype = wt.DWORD
k32.GetThreadContext.argtypes = [wt.HANDLE, ctypes.c_void_p]
k32.GetThreadContext.restype = wt.BOOL
k32.QueryThreadCycleTime.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_uint64)]
k32.QueryThreadCycleTime.restype = wt.BOOL
psapi.EnumProcessModules.argtypes = [wt.HANDLE, ctypes.POINTER(ctypes.c_void_p), wt.DWORD, ctypes.POINTER(wt.DWORD)]
psapi.EnumProcessModules.restype = wt.BOOL
psapi.GetModuleInformation.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.POINTER(MODULEINFO), wt.DWORD]
psapi.GetModuleInformation.restype = wt.BOOL

CATS = ['NNUE accumulator update', 'NNUE accumulator refresh', 'NNUE output layer', 'Hand-crafted evaluation',
        'Transposition table', 'Move generation', 'Move ordering', 'Make/unmake and legality', 'Search own code', 'Other']
ENGINE_CPP = ('bitboard.cpp', 'board.cpp', 'book.cpp', 'eval.cpp', 'eval_params.cpp', 'nnue.cpp', 'search.cpp', 'uci.cpp')


def classify(frames):
    """frames: innermost first, (function, file basename, line). Returns (category, deciding function)."""
    for fn, fname, _ in frames:
        if 'nnue::update' in fn or 'nnue::dirty_pieces' in fn or 'Worker::record_move' in fn or 'Worker::record_null_move' in fn:
            return CATS[0], fn
        if 'nnue::refresh' in fn:
            return CATS[1], fn
        if 'nnue::evaluate' in fn:
            return CATS[2], fn
        if 'TranspositionTable::' in fn:
            return CATS[4], fn
        if 'Board::generate_' in fn or 'MovePicker::generate_' in fn:
            return CATS[5], fn
        if 'MovePicker::' in fn:
            return CATS[6], fn
        if fname in ('eval.cpp', 'eval_params.cpp'):
            return CATS[3], fn
        if fname in ('board.cpp', 'bitboard.cpp'):
            return CATS[7], fn
        if fname == 'search.cpp':
            if 'sort' in fn.lower() or 'history' in fn.lower():
                return CATS[6], fn
            return CATS[8], fn
        if fname in ('uci.cpp', 'book.cpp'):
            return CATS[9], fn
        # nnue.cpp helpers (add_feature, weights) and header code: keep walking outwards
    return CATS[9], (frames[0][0] if frames else '?? (unresolved)')


def thread_ids(pid):
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    out = []
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(THREADENTRY32)
    ok = k32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            out.append(te.th32ThreadID)
        ok = k32.Thread32Next(snap, ctypes.byref(te))
    k32.CloseHandle(snap)
    return out


def image_range(hproc):
    mods = (ctypes.c_void_p * 8)()
    need = wt.DWORD()
    if not psapi.EnumProcessModules(hproc, mods, ctypes.sizeof(mods), ctypes.byref(need)):
        raise RuntimeError('EnumProcessModules failed (%d)' % ctypes.get_last_error())
    info = MODULEINFO()
    if not psapi.GetModuleInformation(hproc, mods[0], ctypes.byref(info), ctypes.sizeof(info)):
        raise RuntimeError('GetModuleInformation failed (%d)' % ctypes.get_last_error())
    return info.lpBaseOfDll, info.SizeOfImage


def profile_once(a, mask):
    hist = collections.Counter()
    eng = U.Engine(a.exe, mask)
    eng.uci()
    eng.setoption('Threads', 1)
    eng.setoption('UseNNUE', 'true' if a.net == 'on' else 'false')
    eng.isready()
    eng.bench(11, 600)                                 # warm-up: tables, weights and code pages touched
    hproc = wt.HANDLE(int(eng.p._handle))
    base, size = image_range(hproc)
    handles, last = {}, {}
    cyc = ctypes.c_uint64()

    def refresh_threads():
        for tid in thread_ids(eng.p.pid):
            if tid not in handles:
                h = k32.OpenThread(THREAD_ACCESS, False, tid)
                if h:
                    handles[tid] = h
                    k32.QueryThreadCycleTime(h, ctypes.byref(cyc))
                    last[tid] = cyc.value

    refresh_threads()
    raw = ctypes.create_string_buffer(CONTEXT_SIZE + 16)
    ctx = (ctypes.addressof(raw) + 15) & ~15
    done = threading.Event()
    result = {}

    def waiter():
        try:
            result['line'] = eng.read_until(lambda s: s.startswith('info string bench depth %d ' % a.depth), 3600)[-1]
        except Exception as e:  # noqa
            result['err'] = str(e)
        finally:
            done.set()

    eng.send('bench %d' % a.depth)
    threading.Thread(target=waiter, daemon=True).start()
    taken = outside = polls = 0
    t0 = time.perf_counter()
    next_refresh = t0 + 1.0
    while not done.is_set():
        time.sleep(0.0005)
        polls += 1
        if time.perf_counter() >= next_refresh:
            refresh_threads()
            next_refresh += 1.0
        for tid, h in handles.items():
            if not k32.QueryThreadCycleTime(h, ctypes.byref(cyc)):
                continue
            if cyc.value - last[tid] < a.quantum:
                continue
            last[tid] = cyc.value
            if k32.SuspendThread(h) == 0xFFFFFFFF:
                continue
            try:
                ctypes.c_uint32.from_address(ctx + OFF_FLAGS).value = CONTEXT_CONTROL
                ok = k32.GetThreadContext(h, ctx)
                rip = ctypes.c_uint64.from_address(ctx + OFF_RIP).value if ok else 0
            finally:
                k32.ResumeThread(h)
            if not ok:
                continue
            taken += 1
            if base <= rip < base + size:
                hist[rip - base] += 1
            else:
                outside += 1
    wall = time.perf_counter() - t0
    for h in handles.values():
        k32.CloseHandle(h)
    code = eng.quit()
    info = {'bench_line': result.get('line'), 'error': result.get('err'), 'wall_s': round(wall, 2), 'samples': taken,
            'outside_image': outside, 'polls': polls, 'threads_seen': len(handles), 'engine_exit': code,
            'child_mask': '0x%X' % eng.child_mask}
    return hist, info


def symbolize(symexe, rvas):
    cmd = [os.path.join(LLVM, 'llvm-symbolizer.exe'), '--obj=' + symexe, '--relative-address', '--inlines',
           '--functions=linkage', '--demangle', '--output-style=JSON']
    inp = '\n'.join(hex(r) for r in rvas) + '\n'
    p = U.spawn(cmd, U.self_affinity(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    so, se = p.communicate(inp.encode('ascii'))
    out = {}
    for line in so.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if not line.startswith('{'):
            continue
        try:
            o = json.loads(line)
        except ValueError:
            continue
        frames = [(f.get('FunctionName') or '??', os.path.basename((f.get('FileName') or '').replace('\\', '/')), f.get('Line') or 0)
                  for f in o.get('Symbol', [])]
        out[int(o['Address'], 16)] = [f for f in frames if f[0] not in ('??', '')]
    if p.returncode != 0 or not out:
        print('symbolizer stderr: ' + se.decode('utf-8', 'replace')[:400], flush=True)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--exe', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--log', required=True)
    p.add_argument('--mask', required=True)
    p.add_argument('--depth', type=int, default=22)
    p.add_argument('--net', choices=['on', 'off'], default='on')
    p.add_argument('--quantum', type=int, default=1_500_000)
    p.add_argument('--repeat', type=int, default=2)
    p.add_argument('--expect-nodes', type=int, default=34048354)
    a = p.parse_args()
    U.require_lane()
    mask = U.parse_mask(a.mask)
    os.makedirs(a.out, exist_ok=True)
    symexe = os.path.join(a.out, 'sym_nodwarf.exe')
    if not os.path.exists(symexe):
        r = U.spawn([os.path.join(LLVM, 'llvm-objcopy.exe'), '--strip-debug', a.exe, symexe], U.self_affinity())
        if r.wait() != 0:
            raise SystemExit('llvm-objcopy failed')
    L = U.header('PROFILE (instruction-pointer sampling)', [os.path.abspath(__file__), U.__file__], [a.exe, symexe], [
        'workload: bench %d, net %s, Threads 1, bench uses its own 16 MB table; warm-up bench 11 before sampling' % (a.depth, a.net),
        'engine pinned to mask 0x%X; sampler process on mask 0x%X; quantum %d thread cycles; planned runs %d' % (mask, U.self_affinity(), a.quantum, a.repeat),
        'category rule: innermost frame naming a listed function or written in an engine .cpp file; header helpers are charged to their caller; outside-image and unresolved samples are Other'])
    per_run, total_hist, outside_all, valid = [], collections.Counter(), 0, 0
    for i in range(a.repeat):
        hist, info = profile_once(a, mask)
        ok = bool(info['bench_line']) and (' nodes %d ' % a.expect_nodes) in (info['bench_line'] or '') and info['engine_exit'] == 0
        valid += 1 if ok else 0
        L.append('run %d: %s; samples %d (outside the engine image %d); wall %.1f s; threads seen %d; exit %s; child mask %s; %s; %s' % (
            i + 1, 'VALID' if ok else 'INVALID', info['samples'], info['outside_image'], info['wall_s'], info['threads_seen'],
            info['engine_exit'], info['child_mask'], info['bench_line'], info['error'] or 'no error'))
        with open(os.path.join(a.out, 'rva_hist_run%d.tsv' % (i + 1)), 'w', encoding='ascii', newline='\n') as f:
            for rva, n in sorted(hist.items()):
                f.write('%#x\t%d\n' % (rva, n))
        per_run.append((hist, info['outside_image']))
        total_hist.update(hist)
        outside_all += info['outside_image']
    sym = symbolize(symexe, sorted(total_hist))

    def tables(hist, outside):
        cat, fn, ln = collections.Counter(), collections.Counter(), collections.Counter()
        unresolved = 0
        for rva, n in hist.items():
            frames = sym.get(rva) or []
            if not frames:
                unresolved += n
            c, f = classify(frames)
            cat[c] += n
            fn['%s | %s' % (c, (frames[0][0] if frames else '?? (unresolved)')[:110])] += n
            if frames:
                ln['%s:%s [%s]' % (frames[0][1], frames[0][2], frames[0][0][:70])] += n
        cat[CATS[9]] += outside
        fn['%s | (outside the engine image: system libraries)' % CATS[9]] += outside
        return cat, fn, ln, unresolved, sum(hist.values()) + outside

    L.append('')
    L.append('CATEGORY SHARES (percent of all samples of the run; they add to 100)')
    L.append('%-28s %10s %10s %10s' % ('category', 'run 1', 'run 2' if a.repeat > 1 else '-', 'all runs'))
    cols = [tables(h, o) for h, o in per_run] + [tables(total_hist, outside_all)]
    for c in CATS:
        vals = ['%6.2f' % (100.0 * t[0][c] / max(t[4], 1)) for t in cols]
        if a.repeat == 1:
            vals.insert(1, '-')
        L.append('%-28s %10s %10s %10s' % (c, vals[0], vals[1], vals[-1]))
    L.append('%-28s %10s %10s %10s' % ('sample total', cols[0][4], cols[1][4] if a.repeat > 1 else '-', cols[-1][4]))
    L.append('unresolved samples inside the image (counted in Other): ' + ', '.join(str(t[3]) for t in cols))
    L.append('')
    L.append('TOP SOURCE FUNCTIONS, all runs (share %, samples, category | innermost source function)')
    allc = cols[-1]
    for key, n in allc[1].most_common(45):
        L.append('%6.2f %7d  %s' % (100.0 * n / max(allc[4], 1), n, key))
    L.append('')
    L.append('TOP SOURCE LINES, all runs (share %, samples, file:line [function])')
    for key, n in allc[2].most_common(30):
        L.append('%6.2f %7d  %s' % (100.0 * n / max(allc[4], 1), n, key))
    L.append('')
    L.append('planned runs %d completed valid %d' % (a.repeat, valid))
    L.append('VERDICT PROFILE %s; end %s' % ('DONE' if valid == a.repeat else 'INCOMPLETE', U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L))
    return 0 if valid == a.repeat else 2


if __name__ == '__main__':
    raise SystemExit(main())
