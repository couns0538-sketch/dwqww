#!/usr/bin/env python3
"""Write rows [start, stop) of a .pos/.hce pair (fen2bin / hce_dump formats) to a new pair (read-only inputs).
.pos: b"FPOS", u32 version 1, u64 n, then n*32 board bytes, n int16 scores, n uint8 meta.
.hce: b"FHCE", u32 version 1, u64 n, then n int16.
usage: opus_s09_split_pos.py IN.pos IN.hce START STOP OUT_STEM   (writes OUT_STEM.pos / OUT_STEM.hce; refuses to overwrite)"""
from __future__ import annotations
import struct, sys
from pathlib import Path

import numpy as np


def main(argv=None):
    pos, hce, start, stop, stem = (argv or sys.argv[1:])
    start, stop = int(start), int(stop)
    hp = Path(pos).read_bytes()[:16]
    assert hp[:4] == b"FPOS" and struct.unpack("<I", hp[4:8])[0] == 1
    n = struct.unpack("<Q", hp[8:16])[0]
    hh = Path(hce).read_bytes()[:16]
    assert hh[:4] == b"FHCE" and struct.unpack("<Q", hh[8:16])[0] == n
    assert 0 <= start < stop <= n
    m = stop - start
    b = np.memmap(pos, np.uint8, "r", 16, (n, 32))[start:stop]
    s = np.memmap(pos, np.int16, "r", 16 + n * 32, (n,))[start:stop]
    t = np.memmap(pos, np.uint8, "r", 16 + n * 34, (n,))[start:stop]
    h = np.memmap(hce, np.int16, "r", 16, (n,))[start:stop]
    out_pos, out_hce = Path(stem + ".pos"), Path(stem + ".hce")
    for p in (out_pos, out_hce):
        if p.exists():
            raise SystemExit(f"{p} exists")
    with open(out_pos, "xb") as f:
        f.write(b"FPOS" + struct.pack("<IQ", 1, m) + np.ascontiguousarray(b).tobytes()
                + np.ascontiguousarray(s).astype("<i2").tobytes() + np.ascontiguousarray(t).tobytes())
    with open(out_hce, "xb") as f:
        f.write(b"FHCE" + struct.pack("<IQ", 1, m) + np.ascontiguousarray(h).astype("<i2").tobytes())
    print(f"{out_pos.name}/{out_hce.name}: rows {start}..{stop} ({m}) of {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
