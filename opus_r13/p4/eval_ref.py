#!/usr/bin/env python3
"""eval_ref.py - R13 P4 parity reference (own code): Forge v2 static eval of exported FORGENN2 nets in numpy float32.

usage: python -I -B eval_ref.py <net.nnue2> <features.txt> <fens.txt> <out.txt>
  features.txt = `forge_v2_bullet features <stage> <fens.txt>` (per FEN: W|B, "S <side-to-move indices>", "N <other>")
Math = forge/nnue_v2.hpp, replayed in its float32 order:
  accumulator = b1 + sum of the active columns (int16 / 4096; every partial sum is a multiple of 2^-12 below 2^12, so the
  sum is exact in float32 whatever the order: computed in int64 here, then one exact conversion);
  lanes[L] = sum over h = L, L + 16, ... of (a*a)*w2[h] + (b*b)*w2[H + h], a / b = side-to-move / other accumulator
  clamped to [0, 1], each product and sum rounded to float32 (no FMA: -ffp-contract=off) - the AVX2, SSE and scalar
  paths of nnue::v2::output all map hidden unit h to lane h % 16;
  out = b2[bucket] + lanes[0] + ... + lanes[15] (in that order); cp = trunc((out * 400) / 2.25) clamped to +-30000;
  bucket = output_map[number of pieces on the board].
Column numbering = forge_v2_bullet (768 piece-square, then threats, then pawn pairs). Writes one cp per FEN.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import forge_nnue_v2 as v2  # noqa: E402

F32 = np.float32


def main():
    net_path, feat_path, fen_path, out_path = sys.argv[1:5]
    net = v2.read_v2(net_path)
    h = net['hidden']
    w1 = np.asarray(net['w1'], dtype=np.int64).reshape(-1, h)
    blocks = [w1]
    if net.get('wt') is not None:
        blocks.append(np.asarray(net['wt'], dtype=np.int64).reshape(-1, h))
    if net.get('wp') is not None:
        blocks.append(np.asarray(net['wp'], dtype=np.int64).reshape(-1, h))
    cols = np.concatenate(blocks, axis=0)
    b1 = np.asarray(net['b1'], dtype=np.int64)
    w2 = (np.asarray(net['w2'], dtype=np.int64).astype(np.float64) / 4096.0).astype(F32).reshape(-1, 2 * h)
    b2 = (np.asarray(net['b2'], dtype=np.int64).astype(np.float64) / 4096.0).astype(F32)
    omap = list(net['output_map'])
    fens = [l.strip() for l in open(fen_path) if l.strip()]
    lines = [l.rstrip('\n') for l in open(feat_path)]
    assert len(lines) == 3 * len(fens), (len(lines), len(fens))
    out = []
    for i, fen in enumerate(fens):
        s_idx = [int(x) for x in lines[3 * i + 1].split()[1:]]
        n_idx = [int(x) for x in lines[3 * i + 2].split()[1:]]
        acc_s = ((b1 + cols[s_idx].sum(axis=0)).astype(np.float64) / 4096.0).astype(F32)
        acc_n = ((b1 + cols[n_idx].sum(axis=0)).astype(np.float64) / 4096.0).astype(F32)
        pieces = sum(ch.isalpha() for ch in fen.split()[0])
        bucket = omap[pieces]
        a = np.clip(acc_s, F32(0), F32(1))
        b = np.clip(acc_n, F32(0), F32(1))
        terms = (a * a) * w2[bucket, :h] + (b * b) * w2[bucket, h:]   # float32 elementwise, products then sum
        terms = terms.astype(F32).reshape(h // 16, 16)
        lanes = np.zeros(16, dtype=F32)
        for k in range(h // 16):
            lanes = (lanes + terms[k]).astype(F32)
        o = F32(b2[bucket])
        for j in range(16):
            o = F32(o + lanes[j])
        cp = F32(F32(o * F32(400.0)) / F32(2.25))
        out.append(int(max(-30000.0, min(30000.0, float(cp)))))   # static_cast<int> truncates toward zero
    with open(out_path, 'w', newline='\n') as fh:
        fh.write(''.join(f'{c}\n' for c in out))
    print(f'{len(out)} evals written to {out_path} (net {os.path.basename(net_path)}, hidden {h})')


if __name__ == '__main__':
    main()
