#!/usr/bin/env python3
"""make_random_net.py - R13 P4 (own code): a FORGENN2 file with seeded random int16 weights, per stage, for the feature /
layout parity test (no training needed: bullet da426a49 has no CPU backend, its mock runtime cannot run).

usage: python -I -B make_random_net.py <stage a|b|c> <out.nnue2> [--hidden 256] [--seed 13451]
Weights are uniform in [-1500, 1500] (|w| / 4096 < 0.37), biases in [-800, 800]: with ~150 active inputs the accumulators
stay far below 2^12, so every float32 accumulator sum is exact (the property Forge relies on), while about half of the
hidden units land inside the SCReLU clamp range [0, 1] and the output buckets differ.
"""
import argparse
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_nnue_v2 as v2  # noqa: E402

PSQ, THREATS, PAIRS, BUCKETS = 768, 12 * 12 * 64, 4 * 7 * 64, 8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['a', 'b', 'c'])
    ap.add_argument('out')
    ap.add_argument('--hidden', type=int, default=256)
    ap.add_argument('--seed', type=int, default=13451)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit(f'refusing to overwrite {a.out}')
    rng = random.Random(a.seed)
    h = a.hidden
    rw = lambda n, lim: [rng.randint(-lim, lim) for _ in range(n)]
    threats, pairs = a.stage in 'bc', a.stage == 'c'
    feature_set = (v2.FEATURE_SET_THREATS if threats else 0) | (v2.FEATURE_SET_PAWN_PAIRS if pairs else 0)
    checksum = v2.write_v2(a.out, hidden=h, king_buckets=1, residual=False, mirror=False, king_map=[0] * 64,
                           w1=rw(PSQ * h, 1500), b1=rw(h, 800), w2=rw(BUCKETS * 2 * h, 1500), b2=rw(BUCKETS, 800),
                           output_buckets=BUCKETS, output_map=v2.output_layout(BUCKETS), feature_set=feature_set,
                           wt=rw(THREATS * h, 1500) if threats else None, wp=rw(PAIRS * h, 1500) if pairs else None)
    print(f'{a.out}: stage {a.stage}, seed {a.seed}, hidden {h}, feature_set {feature_set}, fnv1a64 {checksum:016x}')


if __name__ == '__main__':
    main()
