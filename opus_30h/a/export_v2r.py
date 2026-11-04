#!/usr/bin/env python3
"""export_v2r.py - Opus 30-h job: forge-v2-bullet `r` mode checkpoint (raw f32 quantised.bin) -> FORGENN2 residual net.

usage: python -I -B export_v2r.py <quantised.bin> <out.nnue2> --kb-map one|rank4 [--mirror] [--hidden 256] [--stand-alone]
       python -I -B export_v2r.py --make-test <out quantised.bin> --kb-map ... [--hidden 256] --seed S
           (writes a synthetic quantised.bin in the same layout from random values, to test this exporter with the
           engine parity tools before any GPU run)
Layout (R13 P4 export_v2.py, the library's save format of forge_v2_bullet): all raw f32 little-endian:
  l0w [inputs][H] (one column of H per input), l0b [H], l1w [8][2H] (saved transposed: side to move first), l1b [8],
  then padding to a multiple of 64 bytes with the repeating bytes b"bullet" (or none); inputs = king buckets * 768.
Quantisation q = round-half-away-from-zero(x * 4096); |q| > 32767 or a non-finite value is an error (never clipped).
The `r` mode trains with the residual base (hand-crafted evaluation added before the loss), so the file gets the
residual flag (Forge adds its own HCE), unless --stand-alone. Output buckets = 8, Forge's default map.
"""
import argparse
import math
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import king_map, output_map, write_v2  # noqa: E402

BUCKETS = 8


def quantise(a, name):
    if not np.all(np.isfinite(a)):
        raise SystemExit(f'{name}: non-finite weight')
    q = np.floor(np.abs(a.astype(np.float64)) * 4096.0 + 0.5) * np.sign(a)
    if np.any(np.abs(q) > 32767):
        raise SystemExit(f'{name}: a weight overflows int16 at scale 4096 (max |x| {np.abs(a).max()})')
    return q.astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('checkpoint', nargs='?')
    ap.add_argument('out', nargs='?')
    ap.add_argument('--kb-map', required=True, choices=['one', 'rank4'])
    ap.add_argument('--mirror', action='store_true')
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('--stand-alone', action='store_true')
    ap.add_argument('--make-test')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    kmap = king_map(a.kb_map)
    kb, h = max(kmap) + 1, a.hidden
    counts = [kb * 768 * h, h, BUCKETS * 2 * h, BUCKETS]
    need = 4 * sum(counts)
    pad_len = (64 - need % 64) % 64
    pad = (b'bullet' * 11)[:pad_len]
    if a.make_test:
        if os.path.exists(a.make_test):
            raise SystemExit(f'refusing to overwrite {a.make_test}')
        rng = np.random.default_rng(a.seed)
        vals = [rng.uniform(-0.07, 0.07, counts[0]), rng.uniform(0.0, 0.5, counts[1]), rng.uniform(-1.0, 1.0, counts[2]),
                rng.uniform(-0.5, 0.5, counts[3])]
        with open(a.make_test, 'xb') as f:
            f.write(np.concatenate(vals).astype('<f4').tobytes() + pad)
        print(f'wrote test checkpoint {a.make_test}: kb {kb} hidden {h}, {need} bytes + {pad_len} padding')
        return
    if not a.checkpoint or not a.out:
        raise SystemExit(__doc__)
    raw = open(a.checkpoint, 'rb').read()
    if not (len(raw) == need or (len(raw) == need + pad_len and raw[need:] == pad)):
        raise SystemExit(f'{a.checkpoint}: {len(raw)} bytes; expected {need} (kb {kb}, H {h}) or {need + pad_len} with '
                         f'the library padding; tail {raw[need:need + 16]!r}')
    f = np.frombuffer(raw, '<f4', count=need // 4)
    parts, pos = [], 0
    for c in counts:
        parts.append(f[pos:pos + c])
        pos += c
    l0w, l0b, l1w, l1b = parts
    w1 = quantise(l0w, 'l0w').reshape(kb, 768, h)
    csum = write_v2(a.out, w1, quantise(l0b, 'l0b'), quantise(l1w, 'l1w').reshape(BUCKETS, 2 * h), quantise(l1b, 'l1b'),
                    kmap, output_map(BUCKETS), residual=not a.stand_alone, mirror=a.mirror)
    print(f'wrote {a.out}: kb {kb} ({a.kb_map}){" mirrored" if a.mirror else ""} hidden {h} output buckets {BUCKETS} '
          f'{"stand-alone" if a.stand_alone else "residual"} fnv1a {csum:016x}')


if __name__ == '__main__':
    main()
