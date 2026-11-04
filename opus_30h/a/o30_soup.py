#!/usr/bin/env python3
"""o30_soup.py - Opus 30-h job: uniform weight average ("soup") of forge-v2-bullet `r` checkpoints of one shape.

usage: python -I -B o30_soup.py --kb-map rank4x4 [--hidden 256] --out <soup quantised.bin> <quantised.bin> <quantised.bin> ...
Every input must be a raw f32 quantised.bin of the same king map and hidden size (the layout export_v2r.py reads:
l0w, l0b, l1w, l1b, then the library padding or none). The float region is averaged element by element in float64
and written as f32 with the first input's padding; export_v2r.py then turns it into a FORGENN2 net like any
checkpoint. Meant for nets trained from the SAME warm start (the lock net) with different seeds, which stay close to
each other. Refuses an existing output; prints each input's md5 and the max |difference| between inputs. Own code.
"""
import argparse
import hashlib
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import KING_MAPS, king_map  # noqa: E402

BUCKETS = 8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kb-map', required=True, choices=list(KING_MAPS))
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('--out', required=True)
    ap.add_argument('inputs', nargs='+')
    a = ap.parse_args()
    if len(a.inputs) < 2:
        raise SystemExit('need at least two checkpoints')
    if os.path.exists(a.out):
        raise SystemExit(f'refusing: {a.out} exists')
    kb, h = max(king_map(a.kb_map)) + 1, a.hidden
    need = 4 * (kb * 768 * h + h + BUCKETS * 2 * h + BUCKETS)
    pad_len = (64 - need % 64) % 64
    pad = (b'bullet' * 11)[:pad_len]
    acc, tail, first = None, None, None
    for path in a.inputs:
        # review W2-09: the size alone cannot tell two maps with the same bucket count apart (or a mirrored run); a
        # checkpoint folder forge_v2r_<map>_h<H>-<n> must name --kb-map / --hidden (expanded copies carry no name)
        for part in re.split(r'[\\/]', path):
            m = re.match(r'forge_v2r_(\w+?)_h(\d+)-\d+$', part)
            if m and (m.group(1) != a.kb_map or int(m.group(2)) != h):
                raise SystemExit(f'{path}: its folder says {m.group(1)} H {m.group(2)}, not {a.kb_map} H {h}')
        raw = open(path, 'rb').read()
        if not (len(raw) == need or (len(raw) == need + pad_len and raw[need:] == pad)):
            raise SystemExit(f'{path}: {len(raw)} bytes, expected {need} (+{pad_len} padding) for {a.kb_map} H {h}')
        f = np.frombuffer(raw, '<f4', count=need // 4).astype(np.float64)
        if not np.all(np.isfinite(f)):
            raise SystemExit(f'{path}: non-finite weight')
        if acc is None:
            acc, tail, first = f.copy(), raw[need:], f
        else:
            acc += f
            print(f'max |difference| to the first input: {np.abs(f - first).max():.6f}  ({path})')
        print(f'input {path} md5 {hashlib.md5(raw).hexdigest()}')
    soup = (acc / len(a.inputs)).astype('<f4')
    with open(a.out, 'xb') as out:
        out.write(soup.tobytes() + tail)
    data = open(a.out, 'rb').read()
    print(f'wrote {a.out}: {len(a.inputs)} checkpoints averaged, {len(data)} bytes, md5 {hashlib.md5(data).hexdigest()}')


if __name__ == '__main__':
    main()
