#!/usr/bin/env python3
"""o30_v2ref.py - Opus 30-h job: independent float32 reference of the Forge v2 net output (own code; numpy +
python-chess for FEN parsing). Written from the file-format / feature specification in the engine's
include/forge/nnue_v2.hpp header comment, not from the engine's code, so engine == reference is a real check of the
loader, feature indices (king buckets, mirroring, rank flip), output-bucket choice and the output arithmetic.

usage: python -I -B o30_v2ref.py <net.nnue2> <fens.txt> <out.txt> [--mutate]
  one line per FEN: the network centipawns (int, truncated like the engine), or ERR for an unparsable FEN.
  --mutate adds +1 to the first line (planted bug: a comparison against the engine must then fail).

Arithmetic (float32 throughout, the order of the engine's kernels):
  acc_p = b1 + sum of w1 columns (all values are multiples of 2^-12 below 2^12: exact in any order)
  lanes[j] (j = h mod 16) accumulate, for h increasing: (a*a)*w2[h] + (b*b)*w2[H+h], a / b = clamp(acc, 0, 1)
  out = b2 + lanes[0] + ... + lanes[15] (in order); cp = trunc(clamp(out * 400 / 2.25, +-30000))
"""
import os
import sys

import chess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import read_v2  # noqa: E402

F32 = np.float32


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    mutate = '--mutate' in sys.argv[1:]
    if len(args) != 3:
        sys.exit(__doc__)
    net_path, fen_path, out_path = args
    if os.path.exists(out_path):
        sys.exit(f'refusing to overwrite {out_path}')
    n = read_v2(net_path)
    H = n['hidden']
    w1 = n['w1'].astype(F32) / F32(4096.0)          # [kb][768][H]
    b1 = n['b1'].astype(F32) / F32(4096.0)
    w2 = n['w2'].astype(F32) / F32(4096.0)          # [ob][2H]
    b2 = n['b2'].astype(F32) / F32(4096.0)
    kmap, omap, mirror = n['kmap'], n['omap'], n['mirror']
    out = []
    for line in open(fen_path, 'r', encoding='utf-8'):
        fen = line.strip()
        if not fen:
            continue
        try:
            board = chess.Board(fen)
        except ValueError:
            out.append('ERR')
            continue
        pieces = board.piece_map()
        acc = {}
        for p in (chess.WHITE, chess.BLACK):
            ksq = board.king(p)
            kr = ksq if p == chess.WHITE else ksq ^ 56
            flip = 7 if (mirror and (kr & 7) >= 4) else 0
            bucket = kmap[kr]
            a = b1.copy()
            for sq, pc in pieces.items():
                rel_color = 0 if pc.color == p else 1
                r = (sq if p == chess.WHITE else sq ^ 56) ^ flip
                a = a + w1[bucket, (rel_color * 6 + pc.piece_type - 1) * 64 + r]
            acc[p] = a
        ours, theirs = acc[board.turn], acc[not board.turn]
        ob = omap[min(len(pieces), 32)]
        wa, wb = w2[ob, :H], w2[ob, H:]
        lanes = np.zeros(16, dtype=F32)
        for h0 in range(0, H, 16):
            a = np.minimum(np.maximum(ours[h0:h0 + 16], F32(0)), F32(1))
            b = np.minimum(np.maximum(theirs[h0:h0 + 16], F32(0)), F32(1))
            lanes = lanes + ((a * a) * wa[h0:h0 + 16] + (b * b) * wb[h0:h0 + 16])
        o = F32(b2[ob])
        for j in range(16):
            o = F32(o + lanes[j])
        cp = F32(F32(o * F32(400.0)) / F32(2.25))
        cp = min(max(float(cp), -30000.0), 30000.0)
        out.append(str(int(cp)))   # int() truncates toward zero like static_cast<int>
    if mutate and out and out[0] != 'ERR':
        out[0] = str(int(out[0]) + 1)
    with open(out_path, 'w', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print(f'{len(out)} lines -> {out_path}')


if __name__ == '__main__':
    main()
