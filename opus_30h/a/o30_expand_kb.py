#!/usr/bin/env python3
"""o30_expand_kb.py - Opus 30-h job: rewrite a forge-v2-bullet `r` checkpoint (raw f32 quantised.bin) of a coarser
unmirrored king map as the 32-bucket map rank4x8, exactly (the same function).

usage: python -I -B o30_expand_kb.py --from rank4|rank4x2|rank4x4 [--to rank4x8|rank4x4|rank4x2] [--hidden 256] <in> <out>
Every king map here is rank4 x a file split of the same rank groups (relative rank 1, 2, 3-4, 5-8), so each rank4x8
bucket (rank group g, file f) lies inside exactly one bucket of the coarser map; its 768 x H first-layer block is
copied from that bucket. l0b, l1w, l1b are unchanged. The result evaluates every position exactly as the input does,
which lets nets of different layouts trained from the same warm start be averaged (o30_soup.py --kb-map rank4x8).
The mapping is derived from o30_v2net.king_map, and checked: for every king square, coarse bucket == the bucket the
copied block came from. Refuses an existing output. Own code.
"""
import argparse
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import king_map  # noqa: E402

BUCKETS = 8


def layout(kb, h):
    counts = [kb * 768 * h, h, BUCKETS * 2 * h, BUCKETS]
    need = 4 * sum(counts)
    pad_len = (64 - need % 64) % 64
    return counts, need, (b'bullet' * 11)[:pad_len]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='src', required=True, choices=['rank4', 'rank4x2', 'rank4x4'])
    ap.add_argument('--to', dest='dst', default='rank4x8', choices=['rank4x2', 'rank4x4', 'rank4x8'])
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('inp')
    ap.add_argument('out')
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f'refusing: {a.out} exists')
    h = a.hidden
    cmap, fmap = king_map(a.src), king_map(a.dst)
    kc, kf = max(cmap) + 1, max(fmap) + 1
    # fine bucket -> coarse bucket, from the maps themselves; every square of a fine bucket must agree
    f2c = {}
    for sq in range(64):
        prev = f2c.setdefault(fmap[sq], cmap[sq])
        if prev != cmap[sq]:
            raise SystemExit(f'{a.dst} bucket {fmap[sq]} spans {a.src} buckets {prev} and {cmap[sq]}')
    if sorted(f2c) != list(range(kf)):
        raise SystemExit(f'{a.dst} map does not use every bucket')
    counts_c, need_c, pad_c = layout(kc, h)
    counts_f, need_f, pad_f = layout(kf, h)
    raw = open(a.inp, 'rb').read()
    if not (len(raw) == need_c or (len(raw) == need_c + len(pad_c) and raw[need_c:] == pad_c)):
        raise SystemExit(f'{a.inp}: {len(raw)} bytes, expected {need_c} (+{len(pad_c)} padding) for {a.src} H {h}')
    f = np.frombuffer(raw, '<f4', count=need_c // 4)
    l0w = f[:counts_c[0]].reshape(kc, 768 * h)
    rest = f[counts_c[0]:]
    l0w_f = np.stack([l0w[f2c[b]] for b in range(kf)])
    data = np.concatenate([l0w_f.ravel(), rest]).astype('<f4').tobytes()
    assert len(data) == need_f
    with open(a.out, 'xb') as out:
        out.write(data + (pad_f if len(raw) > need_c else b''))
    print(f'{a.inp} ({a.src}, {kc} buckets) -> {a.out} ({a.dst}, {kf} buckets); bucket map fine->coarse '
          f'{[f2c[b] for b in range(kf)]}; md5 {hashlib.md5(open(a.out, "rb").read()).hexdigest()}')


if __name__ == '__main__':
    main()
