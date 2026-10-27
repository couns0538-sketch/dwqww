#!/usr/bin/env python3
"""A2 data needs: how the own-king squares of real Forge self-play positions spread over the king-bucket layouts.

usage: a2_bucket_occupancy.py <file.pos> [<train_rows>]

<file.pos> is an FPOS v1 file (16-byte header, n x 32 nibble boards, n x int16 score, n x u8 meta; see
LA/5_nnue/datagen_and_format/record_format/RECORD_FORMAT_v3b_pos_hce_20261025.md). Every position gives two
training samples for the input layer: White's own king square, and Black's own king square rank-flipped
(square ^ 56), because both perspectives' accumulators are trained on every position. A weight block gets
gradient from a sample when the sample's own-king square maps to that block:
  M<n> (mirrored): block = half-board bucket of the C4 standard layout (files e-h fold onto d-a);
  U<2n>: block = key (files e-h in their own blocks);  R4 / R8: rank zones 1|2|3-4|5-8 / single ranks.
<train_rows> (default 231,900,000 = the live trainer's 29 training shards on 2026-10-27, forge-nnue-data
skill) converts the shares into samples per block per epoch.
"""
import sys
import numpy as np

HALF_ROWS = {
    1: ["0000"] * 8,
    2: ["0000", "0000"] + ["1111"] * 6,
    4: ["0011", "0011", "2222", "2222"] + ["3333"] * 4,
    8: ["0123", "4455", "6666"] + ["7777"] * 5,
    16: ["0123", "4567", "8899", "aabb", "cccc", "dddd", "eeee", "ffff"],
}


def half_layout(n):
    if n == 32:
        return list(range(32))
    return [int(ch, 16) for row in HALF_ROWS[n] for ch in row]


def half_index(sq):
    f, r = sq & 7, sq >> 3
    return r * 4 + (f if f < 4 else 7 - f)


def layouts():
    out = []
    for n in (1, 2, 4, 8, 16, 32):
        h = half_layout(n)
        mirrored = np.array([h[half_index(s)] for s in range(64)])
        split = np.array([h[half_index(s)] + (n if (s & 7) >= 4 else 0) for s in range(64)])
        if n >= 2:
            out.append((f"M{n}", mirrored, n))
        out.append((f"U{2 * n}", split, 2 * n))
    zone4 = [0, 1, 2, 2, 3, 3, 3, 3]
    out.append(("R4", np.array([zone4[s >> 3] for s in range(64)]), 4))
    out.append(("R8", np.array([s >> 3 for s in range(64)]), 8))
    return out


def main():
    path = sys.argv[1]
    train_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 231_900_000
    raw = np.memmap(path, np.uint8, "r")
    assert bytes(raw[:4]) == b"FPOS" and int.from_bytes(bytes(raw[4:8]), "little") == 1
    n = int.from_bytes(bytes(raw[8:16]), "little")
    boards = np.asarray(raw[16:16 + 32 * n]).reshape(n, 32)
    codes = np.empty((n, 64), np.uint8)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    wk = codes == 6
    bk = codes == 12
    wcount, bcount = wk.sum(1), bk.sum(1)
    print(f"file {path}: {n:,} positions; exactly one king per side in {int(((wcount == 1) & (bcount == 1)).sum()):,}")
    ok = (wcount == 1) & (bcount == 1)
    own = np.concatenate([np.argmax(wk[ok], 1), np.argmax(bk[ok], 1) ^ 56])   # own-frame king squares
    samples = len(own)
    hist = np.bincount(own, minlength=64)
    files_eh = int(hist.reshape(8, 8)[:, 4:].sum())
    print(f"perspective samples {samples:,}; own king on files e-h: {files_eh:,} ({100 * files_eh / samples:.2f}%)")
    names = "abcdefgh"
    top = np.argsort(-hist)[:10]
    print("most frequent own-king squares (own frame): " + ", ".join(f"{names[s & 7]}{(s >> 3) + 1} {100 * hist[s] / samples:.2f}%" for s in top))
    print(f"own king on rank 1: {100 * hist[:8].sum() / samples:.2f}%, ranks 1-2: {100 * hist[:16].sum() / samples:.2f}%, "
          f"ranks 5-8: {100 * hist[32:].sum() / samples:.2f}%")
    print()
    print(f"| layout | weight blocks | min share | median share | max share | empty blocks | samples/epoch in the smallest block "
          f"(train rows {train_rows:,} x 2 perspectives x min share) | smallest block / one-block net |")
    print("|---|---|---|---|---|---|---|---|")
    for name, block_of, blocks in layouts():
        cnt = np.bincount(block_of[own], minlength=blocks).astype(np.float64)
        share = cnt / samples
        smallest = share.min()
        print(f"| {name} | {blocks} | {100 * smallest:.3f}% | {100 * np.median(share):.3f}% | {100 * share.max():.2f}% "
              f"| {int((cnt == 0).sum())} | {smallest * 2 * train_rows:,.0f} | 1/{1 / max(smallest, 1e-12):,.0f} |")


if __name__ == "__main__":
    main()
