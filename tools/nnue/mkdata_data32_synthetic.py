import numpy as np, sys
rng = np.random.default_rng(7)
def write(name, n):
    # boards: 64 nibble codes (0 empty, 1..12), ~25% occupied
    codes = np.where(rng.random((n, 64)) < 0.25, rng.integers(1, 13, (n, 64)), 0).astype(np.uint8)
    boards = (codes[:, 0::2] | (codes[:, 1::2] << 4)).astype(np.uint8)
    score = rng.normal(0, 300, n).clip(-3000, 3000).astype(np.int16)
    meta = (rng.integers(0, 2, n) | (rng.integers(0, 3, n) << 1)).astype(np.uint8)
    hce = (score * 0.7 + rng.normal(0, 120, n)).clip(-3000, 3000).astype(np.int16)
    with open(f"{name}.pos", "wb") as f:
        f.write(b"FPOS" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
        f.write(boards.tobytes()); f.write(score.tobytes()); f.write(meta.tobytes())
    with open(f"{name}.hce", "wb") as f:
        f.write(b"FHCE" + (1).to_bytes(4, "little") + n.to_bytes(8, "little")); f.write(hce.tobytes())
sizes = [int(x) for x in sys.argv[2:]]
for i, n in enumerate(sizes):
    write(f"{sys.argv[1]}{i:03d}", n)
