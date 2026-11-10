# san.py - sanitizer set-up check, instrumented builds and instrumented runs (Python standard library only).
#   fixtures: python -I -B san.py fixtures --log L [--mask 0x2]
#   build:    python -I -B san.py build --kind asan|ubsan --tag T --log L [--mask 0x404A]
#   bench:    python -I -B san.py bench --kind asan|ubsan --exe X --log L [--masks 0x2,0x8]
#   mt:       python -I -B san.py mt --kind asan|ubsan|release --exe X --log L [--mask 0x404A]
# A run passes only when its full planned count completed with exit code 0, the expected node counts and no
# sanitizer report. Reports are never suppressed. A plain (uninstrumented) exe cannot give a sanitizer verdict.
import argparse
import os
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402
import pins as P  # noqa: E402

LLVM = r'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'
CLANG = LLVM + r'\clang++.exe'
SRC = U.REPO + r'\forge-combo29'
TESTS = U.REPO + r'\fable_cpu_speed\tests'
SYS = ['--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc']
DEFS = ['-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1', '-DFORGE_SPD_TT_NOTLS=1',
        '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1', '-DFORGE_SPD_PREFETCH_EARLY=1',
        '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1']
BASE = ['-std=c++20', '-O1', '-g', '-fno-omit-frame-pointer', '-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread']
SAN = {'asan': ['-fsanitize=address'], 'ubsan': ['-fsanitize=undefined'], 'tsan': ['-fsanitize=thread']}
# Link-only addition for ASan, used for the fixtures and the engine alike. The first ASan engine link (16:12,
# san_build_asan.log) failed with "duplicate symbol: typeinfo for std::thread::_State": the instrumented copy of
# that typeinfo in the engine objects met the one in the static libstdc++. The two are the same object; the flag
# lets the linker keep one. It changes no compile flag and suppresses no sanitizer check.
LINK_EXTRA = {'asan': ['-Wl,--allow-multiple-definition'], 'ubsan': [], 'tsan': []}
UNITS = ['bitboard', 'board', 'book', 'eval', 'eval_params', 'nnue', 'search', 'uci']
MARKS = ('ERROR: AddressSanitizer', 'runtime error:', 'SUMMARY: AddressSanitizer', 'SUMMARY: UndefinedBehaviorSanitizer',
         'AddressSanitizer:', 'CHECK failed')


def env():
    e = dict(os.environ)
    e['PATH'] = LLVM + ';' + e.get('PATH', '')
    e['TEMP'] = e['TMP'] = U.JOB + r'\tmp'
    e['ASAN_OPTIONS'] = 'halt_on_error=1:detect_leaks=0:print_summary=1'
    e['UBSAN_OPTIONS'] = 'print_stacktrace=1:halt_on_error=0:print_summary=1'
    return e


def run(cmd, mask, timeout=1800):
    p = U.spawn(cmd, mask, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env())
    try:
        so, se = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        so, se = p.communicate()
        return 'TIMEOUT', so.decode('utf-8', 'replace'), se.decode('utf-8', 'replace')
    return p.returncode, so.decode('utf-8', 'replace'), se.decode('utf-8', 'replace')


def report_lines(text):
    return [l for l in text.splitlines() if any(m in l for m in MARKS)]


def fixtures(a):
    mask = U.parse_mask(a.mask)
    work = U.JOB + r'\out\san\fixtures'
    os.makedirs(work, exist_ok=True)
    src = TESTS + r'\san_fixtures.cpp'
    plan = [(1, 'asan', 'heap-buffer-overflow'), (2, 'asan', 'stack-buffer-overflow'), (3, 'asan', 'heap-use-after-free'),
            (4, 'ubsan', 'signed integer overflow'), (5, 'ubsan', 'shift exponent'), (6, 'ubsan', 'out of bounds'),
            (0, 'asan', None), (0, 'ubsan', None)]
    L = U.header('SANITIZER FIXTURES', [os.path.abspath(__file__), U.__file__, src], [CLANG], [
        'compile flags: %s %s <sanitizer flag> -fuse-ld=lld -static; ASan link adds %s' % (' '.join(BASE), ' '.join(SYS), ' '.join(LINK_EXTRA['asan'])),
        'ASAN_OPTIONS=%s; UBSAN_OPTIONS=%s' % (env()['ASAN_OPTIONS'], env()['UBSAN_OPTIONS']),
        'planned: 7 fixtures (3 ASan faults, 3 UBSan faults, 1 clean fixture built once per sanitizer) = 8 builds and runs; plus the ThreadSanitizer compile attempt'])
    ok = 0
    for fx, kind, want in plan:
        exe = os.path.join(work, 'fx%d_%s.exe' % (fx, kind))
        if os.path.exists(exe):
            exe = exe[:-4] + '_r2.exe'
        cmd = [CLANG] + BASE + SYS + SAN[kind] + ['-DFIXTURE=%d' % fx, src, '-o', exe, '-fuse-ld=lld', '-static'] + LINK_EXTRA[kind]
        rc, so, se = run(cmd, mask)
        if rc != 0:
            L.append('fixture %d %s: COMPILE FAILED exit %s: %s' % (fx, kind, rc, (se or so).strip().replace('\n', ' | ')[:600]))
            continue
        rc, so, se = run([exe], mask, 120)
        rep = report_lines(se + so)
        if want is None:
            good = (rc == 0 and not rep)
            L.append('fixture clean under %s: exit %s, report lines %d -> %s' % (kind, rc, len(rep), 'AS EXPECTED (silent)' if good else 'UNEXPECTED'))
        else:
            hit = [l for l in rep if want in l]
            good = bool(hit) and (kind == 'ubsan' or rc not in (0,))
            L.append('fixture %d under %s, wants "%s": exit %s -> %s | %s' % (fx, kind, want, rc, 'REPORTED AS EXPECTED' if good else 'NOT REPORTED',
                                                                       (hit[0] if hit else (rep[0] if rep else (se + so).strip()[:200])).strip()[:220]))
        ok += 1 if good else 0
    rc, so, se = run([CLANG] + BASE + SYS + SAN['tsan'] + ['-DFIXTURE=0', src, '-o', os.path.join(work, 'fx0_tsan.exe'), '-fuse-ld=lld', '-static'], mask)
    tsan_msg = (se or so).strip().replace('\n', ' | ')[:300]
    L.append('ThreadSanitizer compile attempt (-fsanitize=thread): exit %s: %s' % (rc, tsan_msg))
    L.append('ThreadSanitizer available: %s' % ('NO (compiler refuses the option for this target)' if rc != 0 else 'yes'))
    L.append('planned 8 completed 8 as expected %d' % ok)
    L.append('VERDICT FIXTURES %s; end %s' % ('PASS' if ok == 8 else 'FAIL', U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L))
    return 0 if ok == 8 else 1


def build(a):
    mask = U.parse_mask(a.mask)
    U.disk_guard(31.1)
    root = os.path.join(U.JOB, 'out', 'build', a.tag)
    if os.path.exists(root):
        raise SystemExit('refusing: %s exists' % root)
    os.makedirs(os.path.join(root, 'obj'))
    L = U.header('SANITIZER BUILD %s (%s)' % (a.tag, a.kind), [os.path.abspath(__file__), U.__file__], [CLANG], [
        'source %s at %s; no LTO, no PGO; mask 0x%X' % (SRC, U.SOURCE_REV, mask)])
    res = {}

    def cc(u):
        o = os.path.join(root, 'obj', u + '.o')
        cmd = [CLANG] + BASE + DEFS + ['-I' + SRC + r'\include'] + SYS + SAN[a.kind] + ['-c', os.path.join(SRC, 'src', u + '.cpp'), '-o', o]
        res[u] = (cmd,) + run(cmd, mask)

    ts = [threading.Thread(target=cc, args=(u,)) for u in UNITS]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    bad = False
    for u in UNITS:
        cmd, rc, so, se = res[u]
        L.append('CMD: ' + ' '.join(cmd))
        L.append('exit %s %s' % (rc, (se or so).strip().replace('\n', ' | ')[:800]))
        bad = bad or rc != 0
    exe = os.path.join(root, 'forge_%s.exe' % a.kind)
    if not bad:
        cmd = [CLANG] + BASE + DEFS + SYS + SAN[a.kind] + ['-fuse-ld=lld', '-static'] + LINK_EXTRA[a.kind] + [os.path.join(root, 'obj', u + '.o') for u in UNITS] + ['-o', exe]
        rc, so, se = run(cmd, mask)
        L.append('CMD: ' + ' '.join(cmd))
        L.append('exit %s %s' % (rc, (se or so).strip().replace('\n', ' | ')[:800]))
        bad = rc != 0
    marks = 0
    if not bad:
        rc, so, se = run([LLVM + r'\llvm-nm.exe', exe], mask)
        needle = '__asan_' if a.kind == 'asan' else '__ubsan_handle'
        marks = sum(1 for l in so.splitlines() if needle in l)
        rc2, so2, _ = run([LLVM + r'\llvm-objdump.exe', '-p', exe], mask)
        dll = [l.strip() for l in so2.splitlines() if 'DLL Name' in l]
        md5, sha = U.hashes(exe)
        L.append('built %s bytes %d md5 %s sha256 %s' % (exe, os.path.getsize(exe), md5, sha))
        L.append('instrumentation check: %d symbols containing "%s"; imported DLLs: %s' % (marks, needle, ', '.join(dll)))
    verdict = 'DONE' if (not bad and marks > 0) else 'FAIL'
    L.append('VERDICT SANBUILD %s; end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(l for l in L if not l.startswith('CMD')))
    return 0 if verdict == 'DONE' else 1


def bench(a):
    masks = [U.parse_mask(x) for x in a.masks.split(',')]
    work = os.path.join(U.JOB, 'out', 'san', 'runs')
    os.makedirs(work, exist_ok=True)
    names = [n for n in P.ORDER if n.startswith('bench')]
    L = U.header('SANITIZER FULL BENCH (%s)' % a.kind, [os.path.abspath(__file__), U.__file__, P.__file__], [a.exe], [
        'settings: built-in net; UseNNUE true (bench_on) / false (bench_off); Threads 1; bench uses its own 16 MB table',
        'ASAN_OPTIONS=%s; UBSAN_OPTIONS=%s' % (env()['ASAN_OPTIONS'], env()['UBSAN_OPTIONS']),
        'planned %d' % len(names)])
    got, notes, errfiles = {}, [], {}

    def lane(kind, mask):
        ef = os.path.join(work, '%s_bench_%s.stderr.txt' % (a.kind, kind))
        errfiles[kind] = ef
        eng = None
        try:
            eng = U.Engine(a.exe, mask, errfile=ef, env=env())
            notes.append('lane %s: requested mask 0x%X, child mask read back 0x%X' % (kind, mask, eng.child_mask))
            eng.uci(300)
            if kind == 'off':
                eng.setoption('UseNNUE', 'false')
            eng.isready(300)
            for n in [x for x in names if x.startswith('bench_' + kind)]:
                got[n] = eng.bench(int(n.rsplit('_d', 1)[1]), 7200)[0]
            code = eng.quit(300)
            notes.append('lane %s: exit code %s' % (kind, code))
            if code != 0:
                got['exit_' + kind] = code
        except Exception as e:  # noqa
            notes.append('lane %s: FAILED: %s' % (kind, e))
            got['fail_' + kind] = str(e)
            if eng is not None:
                eng.kill()

    ts = [threading.Thread(target=lane, args=(k, masks[i % len(masks)])) for i, k in enumerate(('on', 'off'))]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    L.extend(notes)
    done = mism = 0
    for n in names:
        g = got.get(n)
        if isinstance(g, int):
            done += 1
            mism += 0 if g == P.EXPECT[n] else 1
            L.append('BENCH %-14s expected %-10d got %-10d %s' % (n, P.EXPECT[n], g, 'OK' if g == P.EXPECT[n] else 'DIFF'))
        else:
            L.append('BENCH %-14s expected %-10d got NOT COMPLETED' % (n, P.EXPECT[n]))
    reports = 0
    for kind, ef in sorted(errfiles.items()):
        text = open(ef, 'r', encoding='utf-8', errors='replace').read() if os.path.exists(ef) else ''
        rl = report_lines(text)
        reports += len(rl)
        L.append('stderr of lane %s: %d bytes, sha256 %s, sanitizer report lines %d (%s)' % (kind, len(text), U.hashes(ef)[1] if os.path.exists(ef) else '-', len(rl), ef))
        L.extend('  ' + l.strip()[:230] for l in text.splitlines()[:40])
    failed = [k for k in got if k.startswith(('exit_', 'fail_'))]
    L.append('planned %d completed %d node mismatches %d sanitizer report lines %d lane failures %d' % (len(names), done, mism, reports, len(failed)))
    if reports or mism:
        verdict = 'FAIL'
    elif done == len(names) and not failed:
        verdict = 'PASS'
    else:
        verdict = 'INCOMPLETE'
    L.append('VERDICT SANBENCH %s %s; end %s' % (a.kind, verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L))
    return {'PASS': 0, 'FAIL': 1, 'INCOMPLETE': 2}[verdict]


def mt(a):
    """Multi-thread fixed-node searches: crash / report / illegal-move check. NOT a ThreadSanitizer run."""
    mask = U.parse_mask(a.mask)
    work = os.path.join(U.JOB, 'out', 'san', 'runs')
    os.makedirs(work, exist_ok=True)
    fens = U.read_fens(1, 25)
    threads = list(range(2, 10))
    planned = len(fens) * len(threads)
    ef = os.path.join(work, '%s_mt.stderr.txt' % a.kind)
    L = U.header('MULTI-THREAD FIXED-NODE SEARCHES (%s build) - not a ThreadSanitizer run' % a.kind,
                 [os.path.abspath(__file__), U.__file__], [a.exe, U.LOCK_EXE], [
        'settings: Threads 2..9, Hash 64, go nodes 300000, positions 1-25 of the frozen file (sha256 %s), net on; all threads inside mask 0x%X' % (U.hashes(U.CORPUS)[1], mask),
        'legal move lists come from the lock exe (go perft 1)', 'planned %d searches' % planned])
    done = illegal = 0
    code, err = None, ''
    eng = ref = None
    try:
        ref = U.Engine(U.LOCK_EXE, mask)
        ref.uci()
        ref.isready()
        legal = []
        for f in fens:
            ref.send('position fen ' + f)
            _, lines = ref.perft(1, 120)
            legal.append({l.split(':')[0] for l in lines if ':' in l})
        ref.quit()
        eng = U.Engine(a.exe, mask, errfile=ef, env=env())
        L.append('child mask read back 0x%X' % eng.child_mask)
        eng.uci(300)
        eng.setoption('Hash', 64)
        for t in threads:
            eng.setoption('Threads', t)
            eng.isready(300)
            for i, f in enumerate(fens):
                eng.send('position fen ' + f)
                d, s, n, b = eng.go('nodes 300000', 3600)
                done += 1
                if b not in legal[i]:
                    illegal += 1
                    L.append('ILLEGAL or missing best move: Threads %d position %d: %s' % (t, i + 1, b))
        code = eng.quit(300)
    except Exception as e:  # noqa
        err = str(e)
        for x in (eng, ref):
            if x is not None:
                x.kill()
    text = open(ef, 'r', encoding='utf-8', errors='replace').read() if os.path.exists(ef) else ''
    rl = report_lines(text)
    L.append('stderr: %d bytes, sanitizer report lines %d (%s)' % (len(text), len(rl), ef))
    L.extend('  ' + l.strip()[:230] for l in text.splitlines()[:40])
    if err:
        L.append('ERROR ' + err)
    L.append('planned %d completed %d illegal best moves %d sanitizer report lines %d exit code %s' % (planned, done, illegal, len(rl), code))
    if rl or illegal:
        verdict = 'FAIL'
    elif done == planned and code == 0 and not err:
        verdict = 'PASS'
    else:
        verdict = 'INCOMPLETE'
    L.append('VERDICT MTSOAK %s %s; end %s' % (a.kind, verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L[-8:]))
    return {'PASS': 0, 'FAIL': 1, 'INCOMPLETE': 2}[verdict]


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    f = sub.add_parser('fixtures')
    f.add_argument('--log', required=True)
    f.add_argument('--mask', default='0x2')
    b = sub.add_parser('build')
    b.add_argument('--kind', choices=['asan', 'ubsan'], required=True)
    b.add_argument('--tag', required=True)
    b.add_argument('--log', required=True)
    b.add_argument('--mask', default='0x404A')
    n = sub.add_parser('bench')
    n.add_argument('--kind', choices=['asan', 'ubsan'], required=True)
    n.add_argument('--exe', required=True)
    n.add_argument('--log', required=True)
    n.add_argument('--masks', default='0x2,0x8')
    m = sub.add_parser('mt')
    m.add_argument('--kind', choices=['asan', 'ubsan', 'release'], required=True)
    m.add_argument('--exe', required=True)
    m.add_argument('--log', required=True)
    m.add_argument('--mask', default='0x404A')
    a = ap.parse_args()
    U.require_lane()
    return {'fixtures': fixtures, 'build': build, 'bench': bench, 'mt': mt}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
