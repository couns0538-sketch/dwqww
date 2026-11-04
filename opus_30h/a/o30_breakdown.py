#!/usr/bin/env python3
"""o30_breakdown.py - Opus 30-h job: where does a net's holdout gain over the lock net come from? (own code; numpy)
usage: python -I -B o30_breakdown.py <dump net> <dump lock> [--pos <S31 .pos>] [--out <new .md>]
The two dumps are `o30_score_v3.exe --dump` files of the SAME .pos (per-row b0.6 squared error, -1 = skipped). Groups
the paired per-row difference (net - lock; negative = the net is better) by: output bucket of the OB8 map (piece
count), the side to move's king rank bucket (rank4 map: rank 1 / 2 / 3-4 / 5-8 seen from that side), the other king's
bucket, the label size |score| and the game result from the side to move. Each group: rows, mean difference, its
standard error (sd / sqrt(rows)), z, and the share of the total gain (sum of the group's differences / total sum).
This is the measurement error of a fixed row set, not training noise; groups are not independent tests.
"""
import argparse
import sys

import numpy as np

S16_POS = r'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos'


def rank4(rel_rank):
    return np.select([rel_rank == 0, rel_rank == 1, rel_rank <= 3], [0, 1, 2], 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('net')
    ap.add_argument('lock')
    ap.add_argument('--pos', default=S16_POS)
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    dn = np.fromfile(a.net, np.float64)
    dl = np.fromfile(a.lock, np.float64)
    n = int.from_bytes(open(a.pos, 'rb').read(16)[8:16], 'little')   # FPOS header: row count at bytes 8-15
    if dn.shape != dl.shape or dn.size != n:
        sys.exit(f'dump sizes {dn.size} / {dl.size} do not match the {n} rows of {a.pos}')
    boards = np.fromfile(a.pos, np.uint8, count=32 * n, offset=16).reshape(n, 32)
    score = np.fromfile(a.pos, '<i2', count=n, offset=16 + 32 * n).astype(np.int32)
    meta = np.fromfile(a.pos, np.uint8, count=n, offset=16 + 34 * n)
    keep = (dn >= 0) & (dl >= 0)
    d = dn - dl
    codes = np.empty((n, 64), np.int16)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    count = (codes > 0).sum(1)
    stm = (meta & 1).astype(np.int64)
    white_res = (meta >> 1).astype(np.int64)          # 0 black won, 1 draw, 2 white won
    res_stm = np.where(stm == 0, white_res, 2 - white_res)
    wk = np.argmax(codes == 6, axis=1)
    bk = np.argmax(codes == 12, axis=1)
    stm_k = np.where(stm == 0, wk >> 3, (bk ^ 56) >> 3)
    ntm_k = np.where(stm == 0, (bk ^ 56) >> 3, wk >> 3)
    ob = np.minimum(7, np.maximum(count - 2, 0) * 8 // 32)
    groups = {
        'output bucket (OB8: pieces incl. kings)': (ob, [f'{b} ({", ".join(str(p) for p in range(2, 34) if min(7, max(p - 2, 0) * 8 // 32) == b)} pieces)'[:40] for b in range(8)]),
        'side to move king (rank4 bucket)': (rank4(stm_k), ['rank 1', 'rank 2', 'rank 3-4', 'rank 5-8']),
        'other king (rank4 bucket, its own view)': (rank4(ntm_k), ['rank 1', 'rank 2', 'rank 3-4', 'rank 5-8']),
        'label |score| (cp, side to move)': (np.digitize(np.abs(score), [50, 150, 400, 1000]),
                                             ['0-49', '50-149', '150-399', '400-999', '1000+']),
        'game result (side to move)': (res_stm, ['loss', 'draw', 'win']),
    }
    total = float(d[keep].sum())
    lines = [f'# Holdout breakdown: `{a.net}` vs `{a.lock}`', '',
             f'rows {int(keep.sum()):,}; mean difference {d[keep].mean():+.3e} (net - lock; negative = better); '
             f'SE {d[keep].std(ddof=1) / np.sqrt(keep.sum()):.2e}', '']
    for title, (g, labels) in groups.items():
        lines += [f'## {title}', '', '| group | rows | mean diff | SE | z | share of the gain |', '|---|---|---|---|---|---|']
        for i, lab in enumerate(labels):
            m = keep & (g == i)
            k = int(m.sum())
            if k < 2:
                lines.append(f'| {lab} | {k} | - | - | - | - |')
                continue
            x = d[m]
            se = float(x.std(ddof=1) / np.sqrt(k))
            lines.append(f'| {lab} | {k:,} | {x.mean():+.3e} | {se:.1e} | {x.mean() / se if se > 0 else 0:+.1f} | '
                         f'{100.0 * x.sum() / total if total else 0:.0f} % |')
        lines.append('')
    text = '\n'.join(lines) + '\n'
    print(text)
    if a.out:
        with open(a.out, 'x', encoding='utf-8', newline='\n') as f:
            f.write(text)


if __name__ == '__main__':
    main()
