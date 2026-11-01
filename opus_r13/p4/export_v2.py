#!/usr/bin/env python3
"""export_v2.py - R13 P4: bullet (forge_v2_bullet) raw f32 checkpoint -> Forge FORGENN2 file (own code).

usage: python -I -B export_v2.py <stage a|b|c> <quantised.bin> <out.nnue2> [--hidden 256]

Input: the `quantised.bin` that forge_v2_bullet writes with its save format (all raw f32, little-endian, in order):
  l0w [inputs][H]   (bullet column-major H x inputs = one column of H per input)
  l0b [H]
  l1w [8][2H]       (saved transposed: one row of 2H per output bucket, side-to-move half first)
  l1b [8]
then zero padding to a multiple of 64 bytes (checked: anything else is an error).
inputs = 768 (+ 9216 threats for b, c) (+ 1792 pawn pairs for c), in that order (forge_v2_bullet ForgeV2).
Output: FORGENN2 via the crew's tools/nnue/forge_nnue_v2.py write_v2 (copied unchanged next to this file from
forge-bundle-int b7c17722): hidden H, 1 king bucket (map all 0), no mirroring, stand-alone (not residual), 8 output
buckets with the default map (= bullet MaterialCount<8>), feature_set bit 0 = threats, bit 1 = pawn pairs.
Quantisation: every tensor q = round-half-away-from-zero(x * 4096) (Forge de-quantises int16 / 4096: WeightScale and
OutputScale in forge/nnue.hpp); |q| > 32767 or a non-finite value is an error, never clipped silently.
No FTP1 permutation: FORGENN2 has no int8 L1 layer (hidden -> output directly), so a hidden-unit order has no effect
on any kernel; the permutation applies to the HalfKA (.nnue) path only.
"""
import argparse
import hashlib
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_nnue_v2 as v2  # noqa: E402  (crew tool, unchanged copy)

PSQ, THREATS, PAIRS, BUCKETS = 768, 12 * 12 * 64, 4 * 7 * 64, 8


def quantise(values, name):
    out = []
    for x in values:
        if not math.isfinite(x):
            raise SystemExit(f'{name}: non-finite weight')
        q = int(math.floor(abs(x) * 4096.0 + 0.5)) * (1 if x >= 0 else -1)
        if abs(q) > 32767:
            raise SystemExit(f'{name}: weight {x} overflows int16 at scale 4096')
        out.append(q)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['a', 'b', 'c'])
    ap.add_argument('checkpoint')
    ap.add_argument('out')
    ap.add_argument('--hidden', type=int, default=256)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f'refusing to overwrite {a.out}')
    threats, pairs = a.stage in 'bc', a.stage == 'c'
    n_in = PSQ + (THREATS if threats else 0) + (PAIRS if pairs else 0)
    h = a.hidden
    raw = open(a.checkpoint, 'rb').read()
    counts = [n_in * h, h, BUCKETS * 2 * h, BUCKETS]
    need = 4 * sum(counts)
    if len(raw) < need or len(raw) - need >= 64 or any(raw[need:]):
        raise SystemExit(f'{a.checkpoint}: {len(raw)} bytes, expected {need} + zero padding < 64 (stage {a.stage}, H {h})')
    floats = struct.unpack_from(f'<{need // 4}f', raw)
    pos = 0
    parts = []
    for c in counts:
        parts.append(floats[pos:pos + c])
        pos += c
    l0w, l0b, l1w, l1b = parts
    q0 = quantise(l0w, 'l0w')
    w1 = q0[:PSQ * h]
    wt = q0[PSQ * h:(PSQ + THREATS) * h] if threats else None
    wp = q0[(PSQ + (THREATS if threats else 0)) * h:] if pairs else None
    feature_set = (v2.FEATURE_SET_THREATS if threats else 0) | (v2.FEATURE_SET_PAWN_PAIRS if pairs else 0)
    checksum = v2.write_v2(a.out, hidden=h, king_buckets=1, residual=False, mirror=False, king_map=[0] * 64,
                           w1=w1, b1=quantise(l0b, 'l0b'), w2=quantise(l1w, 'l1w'), b2=quantise(l1b, 'l1b'),
                           output_buckets=BUCKETS, output_map=v2.output_layout(BUCKETS), feature_set=feature_set,
                           wt=wt, wp=wp)
    sha = hashlib.sha256(open(a.out, 'rb').read()).hexdigest()
    print(f'wrote {a.out}: stage {a.stage}, inputs {n_in}, hidden {h}, buckets {BUCKETS}, feature_set {feature_set}, '
          f'fnv1a64 {checksum:016x}, sha256 {sha}')


if __name__ == '__main__':
    main()
