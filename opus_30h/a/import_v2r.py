#!/usr/bin/env python3
"""import_v2r.py - Opus 30-h job: FORGENN2 residual net -> forge-v2-bullet checkpoint for a GPU warm start.

usage: python -I -B import_v2r.py <net.nnue2> <out dir> --kb-map one|rank4|rank4x2 [--mirror]
Writes <out dir>/optimiser_state/weights.bin (+ momentum.bin / velocity.bin of zeros = a fresh AdamW) in the library's
labelled-buffer format (per record: ASCII id, '\\n', u64 little-endian count, count x f32 little-endian), ids l0w, l0b,
l1w, l1b. Values are int16 / 4096 exactly (every int16 / 4096 is exact in f32), so a save without training followed by
export_v2r.py must give the input net back byte for byte (the proof run). Layouts = the inverse of export_v2r.py:
l0w [inputs][H] as stored; l1w is saved transposed, so the stored order is [2H][8] (export reads [8][2H]).
Train with O30_INIT_DIR=<out dir> and O30_CLIP >= max |weight| (the lock net reaches about 3.5; default clip 1.98).
"""
import argparse
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import king_map, output_map, read_v2  # noqa: E402


def record(name, values):
    v = np.ascontiguousarray(values, dtype='<f4').ravel()
    return name.encode('ascii') + b'\n' + struct.pack('<Q', v.size) + v.tobytes()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('net')
    ap.add_argument('out')
    ap.add_argument('--kb-map', required=True, choices=['one', 'rank4', 'rank4x2'])
    ap.add_argument('--mirror', action='store_true')
    a = ap.parse_args()
    n = read_v2(a.net)
    kmap = king_map(a.kb_map)
    if n['kmap'] != list(kmap) or n['mirror'] != a.mirror or not n['residual'] or n['ob'] != 8 or n['omap'] != list(output_map(8)):
        raise SystemExit(f"{a.net}: header does not match --kb-map {a.kb_map} mirror {a.mirror} residual OB8 "
                         f"(kb {n['kb']}, mirror {n['mirror']}, residual {n['residual']}, ob {n['ob']})")
    h, kb = n['hidden'], n['kb']
    l0w = n['w1'].astype(np.float64).reshape(kb * 768, h) / 4096.0          # [inputs][H]
    l0b = n['b1'].astype(np.float64) / 4096.0
    l1w = (n['w2'].astype(np.float64) / 4096.0).T                           # stored [2H][8]
    l1b = n['b2'].astype(np.float64) / 4096.0
    weights = {'l0b': l0b, 'l0w': l0w, 'l1b': l1b, 'l1w': l1w}              # the library writes ids in sorted order
    state = os.path.join(a.out, 'optimiser_state')
    if os.path.exists(a.out):
        raise SystemExit(f'refusing: {a.out} exists')
    os.makedirs(state)
    for fname, zero in (('weights.bin', False), ('momentum.bin', True), ('velocity.bin', True)):
        with open(os.path.join(state, fname), 'xb') as f:
            for name in sorted(weights):
                f.write(record(name, np.zeros(weights[name].size) if zero else weights[name]))
    peak = max(float(np.abs(x).max()) for x in weights.values())
    print(f"wrote {state}: kb {kb} ({a.kb_map}) hidden {h}, max |weight| {peak:.4f} (needs O30_CLIP >= that)")


if __name__ == '__main__':
    main()
