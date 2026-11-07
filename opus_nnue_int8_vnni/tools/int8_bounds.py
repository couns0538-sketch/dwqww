#!/usr/bin/env python3
"""int8_bounds.py - overflow bounds of the NnueInt8Vnni path (own code, 2026-11-06, step 2c).

usage: python -I -B int8_bounds.py <nnue_weights.inc> <nnue_int8_weights.inc>
Proves from the weights alone (no positions):
 1. FT: every int16 accumulator value A = B1q + sum of the active W1q stays inside int16 for ANY position with at most
    one king per side and at most 30 other pieces (a feature = colour, type, square is active at most once). Per hidden
    unit the bound takes the bias, the best own-king and their-king square (or no king) and the 30 most extreme other
    features of each sign. The update code uses two's-complement int16 adds: when the exact final sum fits int16 the
    wrapped result IS that sum, whatever the order of the steps, so incremental == refresh.
 2. SCReLU: c in [0, 255], c*c + 128 <= 65153 < 2^16 (fits u16 lanes), a = (c*c + 128) >> 8 in [0, 254] (u8).
 3. L1: |sum| <= 254 * sum|W2q| < 2^24 (so float(sum) is exact) < 2^31; per vpdpbusd int32 lane (one accumulator,
    512 / 64 = 8 steps of 4 products) <= 32 * 254 * 127.
 4. AVX2 note: pmaddubsw adds two u8*s8 products with SIGNED 16-bit saturation; 2 * 254 * max|W2q| is reported.
Exit 0 = every bound holds, 1 = one fails.
"""
import re
import sys

HIDDEN, INPUTS, FT_SHIFT = 256, 768, 4
INT16_MAX, ACT_MAX = 32767, 255


def parse(text, name):
    m = re.search(r'%s\[(\d+)\]\s*=\s*\{([^}]*)\}' % name, text)
    if not m:
        raise SystemExit('int8_bounds: %s not found' % name)
    return [int(x) for x in m.group(2).replace('\n', ' ').split(',') if x.strip()]


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    t = open(sys.argv[1], 'rb').read().decode('ascii')
    q = open(sys.argv[2], 'rb').read().decode('ascii')
    w1, b1, w2q = parse(t, 'NnueW1'), parse(t, 'NnueB1'), parse(q, 'NnueInt8W2')
    ftq = lambda v: (v + (1 << (FT_SHIFT - 1))) >> FT_SHIFT
    ok = True
    worst, worst_h = 0, -1
    for h in range(HIDDEN):
        col = [ftq(w1[f * HIDDEN + h]) for f in range(INPUTS)]
        king = [[col[(rc * 6 + 5) * 64 + s] for s in range(64)] for rc in (0, 1)]
        other = sorted(col[f] for f in range(INPUTS) if (f // 64) % 6 != 5)
        base = ftq(b1[h])
        hi = base + sum(max(0, max(k)) for k in king) + sum(v for v in other[-30:] if v > 0)
        lo = base + sum(min(0, min(k)) for k in king) + sum(v for v in other[:30] if v < 0)
        m = max(hi, -lo)
        if m > worst:
            worst, worst_h = m, h
    ft_ok = worst <= INT16_MAX
    ok &= ft_ok
    print('1 FT int16 (1/256 units): worst |A| bound %d at hidden unit %d (limit %d): %s; headroom x%.2f' % (
        worst, worst_h, INT16_MAX, 'HOLDS' if ft_ok else 'FAILS', INT16_MAX / worst))
    sq = ACT_MAX * ACT_MAX + 128
    act_ok = sq < 65536 and (sq >> 8) <= 255
    ok &= act_ok
    print('2 SCReLU: c*c + 128 <= %d (< 65536: %s), a <= %d (u8: %s)' % (sq, sq < 65536, sq >> 8, (sq >> 8) <= 255))
    amax = sq >> 8
    s_abs = sum(abs(v) for v in w2q)
    total = amax * s_abs
    lane = 32 * amax * max(abs(v) for v in w2q)
    l1_ok = total < (1 << 24) and lane < (1 << 31)
    ok &= l1_ok
    print('3 L1: sum|W2q| = %d, |sum| <= %d (< 2^24 = 16777216: %s; < 2^31: %s); per int32 lane <= %d' % (
        s_abs, total, total < (1 << 24), total < (1 << 31), lane))
    pair = 2 * amax * max(abs(v) for v in w2q)
    print('4 AVX2 pmaddubsw pair max %d vs int16 %d: %s' % (
        pair, INT16_MAX, 'no saturation' if pair <= INT16_MAX else 'CAN SATURATE (an AVX2 fallback needs a <= 128 or another kernel)'))
    print('VERDICT %s' % ('ALL BOUNDS HOLD' if ok else 'A BOUND FAILS'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
