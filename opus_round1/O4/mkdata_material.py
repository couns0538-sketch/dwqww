#!/usr/bin/env python3
"""O4 learnability data: synthetic records whose teacher score IS a function of the board, in the trainer's
.pos format (layout of 5_nnue/sample_data/data32_sample/mkdata_data32_synthetic.py: header "FPOS", u32 1, u64 n,
then n x 32 nibble-packed boards, n x int16 side-to-move score, n x u8 meta = stm | white_result*2 << 1).

In the archive's sample data the score is random noise independent of the board, so a stand-alone (pure) net
cannot beat predicting the mean there. Here the score is a material count from the side to move's view
(own piece values: pawn 30, knight 90, bishop 100, rook 150, queen 270; king 0) plus small noise, and the
game result is drawn from the score's win probability, so a pure net that learns the whole score from the
board alone must push its holdout loss far below the predict-the-mean level. No .hce files are written
(the pure trainer runs without --hce-dir). Deterministic: the seed is 20261027 plus the bytes of <prefix>, so
the training files (prefix t) and the holdout (prefix h) are different draws.
usage: mkdata_material.py <prefix> <n> [<n> ...]   -> <prefix>000.pos, <prefix>001.pos, ...
"""
import sys

import numpy as np

VALUE = np.array([0, 30, 90, 100, 150, 270, 0, -30, -90, -100, -150, -270, 0], dtype=np.int64)  # by code, White +


def write(rng, name, n):
    codes = np.where(rng.random((n, 64)) < 0.25, rng.integers(1, 13, (n, 64)), 0).astype(np.uint8)
    boards = (codes[:, 0::2] | (codes[:, 1::2] << 4)).astype(np.uint8)
    stm = rng.integers(0, 2, n)
    white_cp = VALUE[codes].sum(axis=1)
    score = (np.where(stm == 0, white_cp, -white_cp) + rng.normal(0, 20, n)).clip(-3000, 3000).astype(np.int16)
    p_white = 1.0 / (1.0 + np.exp(-white_cp * 2.25 / 400.0))
    u = rng.random(n)
    wres = np.where(u < 0.85 * p_white, 2, np.where(u < 0.85 * p_white + 0.15, 1, 0))
    meta = (stm | (wres << 1)).astype(np.uint8)
    with open(f"{name}.pos", "wb") as f:
        f.write(b"FPOS" + (1).to_bytes(4, "little") + int(n).to_bytes(8, "little"))
        f.write(boards.tobytes())
        f.write(score.tobytes())
        f.write(meta.tobytes())
    print(f"{name}.pos: {n} records, score mean {score.mean():.1f} sd {score.std():.1f}")


def main():
    rng = np.random.default_rng(20261027 + sum(sys.argv[1].encode()))
    for i, n in enumerate(int(x) for x in sys.argv[2:]):
        write(rng, f"{sys.argv[1]}{i:03d}", n)


if __name__ == "__main__":
    main()
