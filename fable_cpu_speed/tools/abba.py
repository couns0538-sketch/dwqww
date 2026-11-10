# abba.py - screening timing of two engine exes, pre-registered in PREREG.md (Python standard library only).
# One arm = one new process: uci, isready, bench D, quit (net on, one thread, bench's own 16 MB table).
# A and B alternate (A-B for odd pairs, B-A for even pairs); every arm runs a FRESH COPY of its exe file,
# because a given exe file can carry its own offset of several percent while it stays loaded (job 2 finding).
# Metric: CPU cycles of the whole process (QueryProcessCycleTime) per node; pair value = cycles(A)/cycles(B) - 1,
# so a positive value means B is faster. An arm is valid only with exit 0, the expected node count and
# CPU time / wall time >= 0.97 (not preempted). The result is the median of the measured pair values.
#   python -I -B abba.py --a A.exe --b B.exe --name NAME --log L [--mask 0x1000] [--pairs 12] [--warmup 1]
#                        [--depth 20] [--expect-nodes 12389307] [--label-a lock] [--label-b cand]
import argparse
import os
import shutil
import statistics
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402


def arm(src, tag, workdir, mask, depth, expect):
    dst = os.path.join(workdir, tag + '.exe')
    shutil.copyfile(src, dst)
    if U.hashes(dst)[1] != U.hashes(src)[1]:
        raise SystemExit('copy differs from its source: ' + dst)
    t0 = time.perf_counter()
    p = U.spawn([dst], mask, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=workdir)
    try:
        out, _ = p.communicate(('uci\nisready\nbench %d\nquit\n' % depth).encode('ascii'), timeout=1800)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        return {'tag': tag, 'valid': False, 'why': 'timeout'}
    wall = time.perf_counter() - t0
    h = int(p._handle)
    cyc = U.cycles_of(h)
    cpu = U.cpu_seconds_of(h)
    nodes = ms = -1
    for line in out.decode('ascii', 'replace').splitlines():
        if line.startswith('info string bench depth %d ' % depth):
            tok = line.split()
            nodes = int(tok[tok.index('nodes') + 1])
            ms = int(tok[tok.index('time') + 1])
    why = []
    if p.returncode != 0:
        why.append('exit %s' % p.returncode)
    if nodes != expect:
        why.append('nodes %s' % nodes)
    if wall > 0 and cpu / wall < 0.97:
        why.append('cpu/wall %.3f' % (cpu / wall))
    if cyc <= 0:
        why.append('no cycle count')
    return {'tag': tag, 'valid': not why, 'why': ', '.join(why), 'cycles': cyc, 'cpu_s': cpu, 'wall_s': wall, 'nodes': nodes,
            'bench_ms': ms, 'cpn': (cyc / nodes if nodes > 0 else 0.0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--mask', default='0x1000')
    ap.add_argument('--pairs', type=int, default=12)
    ap.add_argument('--warmup', type=int, default=1)
    ap.add_argument('--depth', type=int, default=20)
    ap.add_argument('--expect-nodes', type=int, default=12389307)
    ap.add_argument('--label-a', default='A')
    ap.add_argument('--label-b', default='B')
    ap.add_argument('--note', default='')
    a = ap.parse_args()
    U.require_lane()
    mask = U.parse_mask(a.mask)
    total = a.pairs + a.warmup
    need_gib = 2 * total * os.path.getsize(a.a) / (1 << 30)
    U.disk_guard(31.0 + need_gib)
    workdir = os.path.join(U.JOB, 'out', 'timing', a.name)
    if os.path.exists(workdir):
        raise SystemExit('refusing: %s exists (one folder per timing run)' % workdir)
    os.makedirs(workdir)
    L = U.header('SCREENING TIMING %s (A = %s, B = %s)' % (a.name, a.label_a, a.label_b), [os.path.abspath(__file__), U.__file__], [a.a, a.b], [
        'workload per arm: new process; uci, isready, bench %d, quit; net on; Threads 1; bench uses its own 16 MB table; identical for A and B' % a.depth,
        'engine mask 0x%X (its SMT sibling is kept free of my work); a fresh copy of the exe file per arm in %s' % (mask, workdir),
        'metric: process CPU cycles per node; pair value = cycles(A)/cycles(B) - 1 (positive = B faster); order A-B for odd pairs, B-A for even pairs',
        'valid arm: exit 0, nodes %d, CPU time / wall time >= 0.97' % a.expect_nodes,
        'planned: %d warm-up pair(s), discarded, then %d measured pairs; fewer than 10 valid pairs = INCONCLUSIVE' % (a.warmup, a.pairs),
        'note: %s' % (a.note or '-')])
    vals = []
    for i in range(1, total + 1):
        order = ('a', 'b') if i % 2 == 1 else ('b', 'a')
        r = {}
        for side in order:
            r[side] = arm(a.a if side == 'a' else a.b, 'p%02d_%s' % (i, side), workdir, mask, a.depth, a.expect_nodes)
        kind = 'warm-up' if i <= a.warmup else 'measured'
        ok = r['a']['valid'] and r['b']['valid']
        v = (r['a']['cycles'] / r['b']['cycles'] - 1.0) if ok else None
        L.append('pair %2d %-8s order %s-%s | A %s cyc/node %.1f bench %s ms cpu/wall %.3f | B %s cyc/node %.1f bench %s ms cpu/wall %.3f | %s' % (
            i, kind, order[0].upper(), order[1].upper(),
            'ok' if r['a']['valid'] else 'INVALID(' + r['a']['why'] + ')', r['a'].get('cpn', 0), r['a'].get('bench_ms'), r['a'].get('cpu_s', 0) / max(r['a'].get('wall_s', 1), 1e-9),
            'ok' if r['b']['valid'] else 'INVALID(' + r['b']['why'] + ')', r['b'].get('cpn', 0), r['b'].get('bench_ms'), r['b'].get('cpu_s', 0) / max(r['b'].get('wall_s', 1), 1e-9),
            ('pair value %+.2f %%' % (100 * v)) if v is not None else 'pair INVALID'))
        if i > a.warmup and v is not None:
            vals.append(100 * v)
    L.append('planned %d measured pairs, valid %d, invalid %d' % (a.pairs, len(vals), a.pairs - len(vals)))
    if vals:
        L.append('pair values %%: %s' % ' '.join('%+.2f' % v for v in vals))
        L.append('RESULT median %+.2f %%, min %+.2f %%, max %+.2f %%, mean %+.2f %%, sd %.2f' % (
            statistics.median(vals), min(vals), max(vals), statistics.mean(vals), statistics.pstdev(vals)))
    verdict = 'DONE' if len(vals) >= 10 else 'INCONCLUSIVE'
    L.append('VERDICT SCREENING %s (screening only: other work ran on this PC; QA\'s quiet ABBA is the speed test); end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L[-(a.pairs + a.warmup + 4):]))
    return 0 if verdict == 'DONE' else 2


if __name__ == '__main__':
    sys.exit(main())
