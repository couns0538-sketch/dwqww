#!/usr/bin/env python3
"""test_soup_tools.py - Opus 30-h job: checks of o30_soup.py and o30_expand_kb.py on small synthetic checkpoints
(export_v2r.py --make-test, H 32) in a new folder under D:\\o30\\tmp. Prints one line per check; exit 0 only if all pass.
  1 soup of a checkpoint with itself = the checkpoint, byte for byte
  2 soup of two checkpoints = their element-wise mean (float64 reference)
  3 o30_soup refuses an existing output and a checkpoint of another shape
  4 expansion rank4 -> rank4x2 -> rank4x4 -> rank4x8: every fine bucket's first-layer block equals the block of the
    coarse bucket of the same king squares (from o30_v2net.king_map); l0b / l1w / l1b unchanged
  5 o30_expand_kb refuses a finer-to-coarser rewrite and an existing output
Own code."""
import os
import subprocess
import sys
import time

import numpy as np

A = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, A)
from o30_v2net import king_map  # noqa: E402

PY = sys.executable
H = 32
ROOT = os.path.join('D:\\o30\\tmp', 'soup_tools_test_' + time.strftime('%Y%m%d_%H%M%S'))
fails = 0


def run(*args):
    return subprocess.run([PY, '-I', '-B', *args], capture_output=True, text=True)


def report(ok, what):
    global fails
    fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {what}")


def floats(path, kmap):
    kb = max(king_map(kmap)) + 1
    n = kb * 768 * H + H + 8 * 2 * H + 8
    f = np.frombuffer(open(path, 'rb').read(), '<f4', count=n)
    return f[:kb * 768 * H].reshape(kb, 768 * H), f[kb * 768 * H:]


def main():
    os.makedirs(ROOT)
    exp, soup = os.path.join(A, 'export_v2r.py'), os.path.join(A, 'o30_soup.py')
    expand = os.path.join(A, 'o30_expand_kb.py')
    ck = {}
    for name, kmap, seed in (('a4', 'rank4', 1), ('b16', 'rank4x4', 2), ('c16', 'rank4x4', 3)):
        ck[name] = os.path.join(ROOT, name + '.bin')
        r = run(exp, '--make-test', ck[name], '--kb-map', kmap, '--hidden', str(H), '--seed', str(seed))
        if r.returncode:
            print(r.stdout, r.stderr)
            sys.exit('cannot make the synthetic checkpoints')
    out1 = os.path.join(ROOT, 'self.bin')
    r = run(soup, '--kb-map', 'rank4x4', '--hidden', str(H), '--out', out1, ck['b16'], ck['b16'])
    report(r.returncode == 0 and open(out1, 'rb').read() == open(ck['b16'], 'rb').read(), '1 self-soup byte-identical')
    out2 = os.path.join(ROOT, 'mean.bin')
    r = run(soup, '--kb-map', 'rank4x4', '--hidden', str(H), '--out', out2, ck['b16'], ck['c16'])
    w2, rest2 = floats(out2, 'rank4x4')
    wb, rb = floats(ck['b16'], 'rank4x4')
    wc, rc = floats(ck['c16'], 'rank4x4')
    ref_w = ((wb.astype(np.float64) + wc) / 2).astype('<f4')
    ref_r = ((rb.astype(np.float64) + rc) / 2).astype('<f4')
    report(r.returncode == 0 and np.array_equal(w2, ref_w) and np.array_equal(rest2, ref_r), '2 two-net soup = element-wise mean')
    r1 = run(soup, '--kb-map', 'rank4x4', '--hidden', str(H), '--out', out2, ck['b16'], ck['c16'])
    r2 = run(soup, '--kb-map', 'rank4x4', '--hidden', str(H), '--out', os.path.join(ROOT, 'x.bin'), ck['b16'], ck['a4'])
    report(r1.returncode != 0 and 'refusing' in (r1.stdout + r1.stderr) and r2.returncode != 0
           and not os.path.exists(os.path.join(ROOT, 'x.bin')), '3 soup refuses an existing output and a wrong shape')
    ok, prev, prev_map = True, ck['a4'], 'rank4'
    for dst in ('rank4x2', 'rank4x4', 'rank4x8'):
        out = os.path.join(ROOT, f'exp_{dst}.bin')
        r = run(expand, '--from', prev_map, '--to', dst, '--hidden', str(H), prev, out)
        if r.returncode:
            ok = False
            print(r.stdout, r.stderr)
            break
        wf, rf = floats(out, dst)
        wco, rco = floats(prev, prev_map)
        cm, fm = king_map(prev_map), king_map(dst)
        ok &= all(np.array_equal(wf[fm[sq]], wco[cm[sq]]) for sq in range(64)) and np.array_equal(rf, rco)
        prev, prev_map = out, dst
    report(ok, '4 expansion chain rank4 -> rank4x2 -> rank4x4 -> rank4x8 copies the right blocks, rest unchanged')
    r1 = run(expand, '--from', 'rank4x4', '--to', 'rank4x2', '--hidden', str(H), ck['b16'], os.path.join(ROOT, 'bad.bin'))
    r2 = run(expand, '--from', 'rank4', '--to', 'rank4x2', '--hidden', str(H), ck['a4'], os.path.join(ROOT, 'exp_rank4x2.bin'))
    report(r1.returncode != 0 and not os.path.exists(os.path.join(ROOT, 'bad.bin')) and r2.returncode != 0
           and 'refusing' in (r2.stdout + r2.stderr), '5 expansion refuses finer-to-coarser and an existing output')
    print(f"soup tools: {5 - fails} PASS, {fails} FAIL (folder {ROOT})")
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
