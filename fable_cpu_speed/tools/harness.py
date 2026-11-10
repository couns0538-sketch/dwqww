# harness.py - build and run the static-evaluation harness tests/evaldump.cpp for one source tree.
#   build: python -I -B harness.py build --src TREE --tag T [--defs FORGE_X=1,FORGE_Y=2] [--mask 0x30]
#   run:   python -I -B harness.py run --tag T [--mask 0x10] [--count 12000]
# The harness is compiled with the lock recipe's compile flags (no LTO, no PGO) plus the given switches. Its two
# transcripts (net on, net off) are written in the row format of rows.py and compared with `rows.py cmp`.
# This is a test binary and separate evidence; see the head of tests/evaldump.cpp.
import argparse
import os
import subprocess
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402

LLVM = r'C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin'
CLANG = LLVM + r'\clang++.exe'
HSRC = U.REPO + r'\fable_cpu_speed\tests\evaldump.cpp'
ROOT = U.JOB + r'\out\harness'
DEFS = ['-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1', '-DFORGE_SPD_TT_NOTLS=1',
        '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1', '-DFORGE_SPD_PREFETCH_EARLY=1',
        '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1']
FLAGS = ['-std=c++20', '-O3', '-ffp-contract=off', '-fno-fast-math', '-march=znver5', '-pthread']
SYS = ['--sysroot=C:/msys64/ucrt64', '-stdlib=libstdc++', '-rtlib=libgcc', '-unwindlib=libgcc']
UNITS = ['bitboard', 'board', 'book', 'eval', 'eval_params', 'nnue', 'search']


def run(cmd, mask, timeout=3600):
    env = dict(os.environ)
    env['PATH'] = LLVM + ';' + env.get('PATH', '')
    env['TEMP'] = env['TMP'] = U.JOB + r'\tmp'
    p = U.spawn(cmd, mask, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    so, se = p.communicate(timeout=timeout)
    return p.returncode, so.decode('utf-8', 'replace'), se.decode('utf-8', 'replace')


def build(a):
    mask = U.parse_mask(a.mask)
    U.disk_guard(31.1)
    root = os.path.join(ROOT, a.tag)
    if os.path.exists(root):
        raise SystemExit('refusing: %s exists' % root)
    os.makedirs(os.path.join(root, 'obj'))
    extra = ['-D' + d for d in a.defs.split(',') if d]
    inc = '-I' + os.path.join(a.src, 'include')
    L = U.header('HARNESS BUILD %s' % a.tag, [os.path.abspath(__file__), U.__file__, HSRC], [CLANG], [
        'source tree %s; extra switches: %s' % (a.src, ' '.join(extra) or '(none)'),
        'flags: %s %s %s; no LTO, no PGO' % (' '.join(FLAGS), ' '.join(DEFS), ' '.join(SYS))])
    res = {}

    def cc(name, path):
        o = os.path.join(root, 'obj', name + '.o')
        res[name] = run([CLANG] + FLAGS + DEFS + extra + [inc] + SYS + ['-c', path, '-o', o], mask)

    jobs = [(u, os.path.join(a.src, 'src', u + '.cpp')) for u in UNITS] + [('evaldump', HSRC)]
    ts = [threading.Thread(target=cc, args=j) for j in jobs]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    bad = False
    for name, _ in jobs:
        rc, so, se = res[name]
        L.append('compile %-12s exit %s %s' % (name, rc, (se or so).strip().replace('\n', ' | ')[:600]))
        bad = bad or rc != 0
    exe = os.path.join(root, 'evaldump.exe')
    if not bad:
        rc, so, se = run([CLANG] + FLAGS + SYS + ['-fuse-ld=lld', '-static'] + [os.path.join(root, 'obj', n + '.o') for n, _ in jobs] + ['-o', exe], mask)
        L.append('link exit %s %s' % (rc, (se or so).strip().replace('\n', ' | ')[:900]))
        bad = rc != 0
    if not bad:
        md5, sha = U.hashes(exe)
        L.append('built %s bytes %d md5 %s sha256 %s' % (exe, os.path.getsize(exe), md5, sha))
    L.append('VERDICT HARNESSBUILD %s; end %s' % ('FAIL' if bad else 'DONE', U.vienna_now()))
    U.write_log(os.path.join(root, 'build.log'), L)
    print('\n'.join(L[-11:]))
    return 1 if bad else 0


def wrap(raw, out, head, planned, code):
    rows = [l for l in open(raw, 'r', encoding='ascii', errors='replace').read().split('\n') if l]
    status = 'COMPLETE' if (code == 0 and len(rows) == planned) else 'INCOMPLETE'
    with open(out, 'w', encoding='ascii', newline='\n') as f:
        f.write(''.join('# ' + x + '\n' for x in head))
        f.write('\n'.join(rows) + '\n')
        f.write('# completed %d of planned %d; engine exit code %s; status %s; end %s\n' % (len(rows), planned, code, status, U.vienna_now()))
    return status, len(rows)


def run_cmd(a):
    mask = U.parse_mask(a.mask)
    U.disk_guard()
    root = os.path.join(ROOT, a.tag)
    exe = os.path.join(root, 'evaldump.exe')
    fens = U.read_fens(1, a.count)
    fl = os.path.join(root, 'fens_%d.txt' % len(fens))
    with open(fl, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(fens) + '\n')
    raw_on, raw_off = os.path.join(root, 'raw_on.txt'), os.path.join(root, 'raw_off.txt')
    rc, so, se = run([exe, fl, raw_on, raw_off], mask)
    res = []
    for net, raw in (('on', raw_on), ('off', raw_off)):
        head = U.header('ROWS harness %s net %s' % (a.tag, net), [os.path.abspath(__file__), U.__file__, HSRC], [exe], [
            'corpus %s sha256 %s; positions 1..%d' % (os.path.basename(U.CORPUS), U.hashes(U.CORPUS)[1], len(fens)),
            'settings: static evaluation through Worker::static_evaluate; net %s; row = root value, raw net, children count:hash, grandchildren count:hash; child mask 0x%X' % (net, mask),
            'harness console: %s %s' % (so.strip(), se.strip()[:300]),
            'planned %d' % len(fens)])
        res.append((net,) + wrap(raw, os.path.join(root, 'eval_%s.tsv' % net), head, len(fens), rc))
    for net, status, n in res:
        print('%s net %s: rows %d of %d, harness exit %s, %s' % (a.tag, net, n, len(fens), rc, status))
    return 0 if all(s == 'COMPLETE' for _, s, _ in res) else 2


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build')
    b.add_argument('--src', required=True)
    b.add_argument('--tag', required=True)
    b.add_argument('--defs', default='')
    b.add_argument('--mask', default='0x30')
    r = sub.add_parser('run')
    r.add_argument('--tag', required=True)
    r.add_argument('--mask', default='0x10')
    r.add_argument('--count', type=int, default=12000)
    a = ap.parse_args()
    U.require_lane()
    return build(a) if a.cmd == 'build' else run_cmd(a)


if __name__ == '__main__':
    sys.exit(main())
